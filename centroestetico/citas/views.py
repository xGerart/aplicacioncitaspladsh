import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import Q, Count, Sum, Avg, Case, When, Value, DecimalField
from django.db.models.functions import TruncMonth, ExtractHour
from django.views.decorators.http import require_GET
from .models import Empleado, Cita, Cliente, Servicio, HorarioEmpleado, HorarioCentro
from .forms import CitaForm
from .decorators import cliente_required, recepcionista_required
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


@login_required
@cliente_required
def agendar_cita(request):
    if request.method == "POST":
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.cliente = request.user.cliente
            cita.servicio_id = request.POST.get("servicio_id")
            cita.estado = Cita.ESTADO_CONFIRMADA

            if cita.hora_inicio:
                cita.save()
                subject = "Confirmación de tu cita"
                html_message = render_to_string(
                    "emails/email_confirmacion_cita.html",
                    {
                        "cita": cita,
                        "cliente": cita.cliente,
                        "centro": {
                            "nombre": "Centro Estético Pladsh",
                            "direccion": "Calle Napo entre Sergio Saenz y Ernesto Rodríguez, Coca, Ecuador",
                        },
                    },
                )
                plain_message = strip_tags(html_message)
                from_email = settings.EMAIL_HOST_USER
                to = cita.cliente.email

                send_mail(
                    subject, plain_message, from_email, [to], html_message=html_message
                )

                messages.success(
                    request,
                    "Cita agendada con éxito. Se ha enviado un correo de confirmación.",
                )
                return redirect("home")
            else:
                messages.error(request, "Por favor, seleccione una hora para la cita.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CitaForm()

    servicios = Servicio.objects.all()
    try:
        horario_cierre = HorarioCentro.objects.get(dia=timezone.now().weekday()).hora_cierre
    except HorarioCentro.DoesNotExist:
        messages.error(request, "No se encontró el horario del centro para el día de hoy.")
        horario_cierre = None

    print(f"Fecha actual: {timezone.now().date()}, Hora de cierre: {horario_cierre}")

    return render(
        request,
        "cita.html",
        {
            "form": form,
            "servicios": servicios,
            "horario_cierre": horario_cierre.strftime("%H:%M"),
        },
    )


@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, cliente__user=request.user)
    if cita.es_cancelable():
        cita.estado = Cita.ESTADO_CANCELADA
        cita.save()
        messages.success(request, "Cita cancelada exitosamente")
    else:
        messages.error(request, "No se puede cancelar esta cita")
    return redirect("home")


@login_required
@recepcionista_required
def gestion_citas(request):
    fecha = request.GET.get("fecha")
    if fecha:
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    else:
        fecha = timezone.now().date()
    citas = Cita.objects.filter(fecha=fecha).select_related(
        "cliente", "servicio", "empleado"
    )
    empleados = Empleado.objects.all()
    return render(
        request,
        "gestion_citas.html",
        {"citas": citas, "empleados": empleados, "fecha": fecha},
    )


@require_GET
def get_empleados_disponibles(request):
    servicio_id = request.GET.get("servicio")
    empleados = Empleado.objects.filter(servicios__id=servicio_id)
    cualquier_empleado = Empleado.get_cualquier_empleado()
    data = {
        "empleados": [
            {"id": emp.id, "nombre": emp.nombre}
            for emp in [cualquier_empleado] + list(empleados)
        ]
    }
    return JsonResponse(data)

@require_GET
def get_bloques_disponibles(request):
    empleado_id = request.GET.get("empleado")
    servicio_id = request.GET.get("servicio")
    fecha_str = request.GET.get("fecha")

    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    dia_semana = fecha.weekday()

    servicio = get_object_or_404(Servicio, id=servicio_id)
    empleados = (
        [get_object_or_404(Empleado, id=empleado_id)]
        if empleado_id != "0"
        else Empleado.objects.filter(servicios__id=servicio_id)
    )

    bloques_disponibles = []
    for empleado in empleados:
        horario = empleado.horarios.filter(
            dia_semana=dia_semana, disponible=True
        ).first()
        if horario:
            hora_actual = horario.hora_inicio
            while hora_actual < horario.hora_fin:
                hora_fin_bloque = (
                    datetime.combine(fecha, hora_actual) + timedelta(minutes=15)
                ).time()
                if hora_fin_bloque <= horario.hora_fin:
                    # Verificar si el bloque está disponible
                    if not Cita.objects.filter(
                        empleado=empleado,
                        fecha=fecha,
                        hora_inicio__lt=hora_fin_bloque,
                        hora_inicio__gte=hora_actual,
                        estado__in=[Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_PROCESO],
                    ).exists():
                        bloques_disponibles.append(
                            {
                                "inicio": hora_actual.strftime("%H:%M"),
                                "empleado_id": empleado.id,
                                "empleado_nombre": empleado.nombre,
                            }
                        )
                hora_actual = hora_fin_bloque

    return JsonResponse(
        {
            "bloques": bloques_disponibles,
            "mensaje": (
                ""
                if bloques_disponibles
                else "No hay horarios disponibles para este día."
            ),
        }
    )


@login_required
def home(request):
    try:
        cliente = request.user.cliente
        if cliente.is_cliente():
            citas = Cita.objects.filter(cliente=cliente).order_by(
                "fecha", "hora_inicio"
            )
            return render(request, "home.html", {"citas": citas})
        elif cliente.is_recepcionista():
            return render(request, "home.html")
        else:
            return render(
                request, "error.html", {"message": "Rol de usuario no reconocido"}
            )
    except Cliente.DoesNotExist:
        return render(
            request, "error.html", {"message": "Perfil de usuario no encontrado"}
        )
    except Exception as e:
        logger.exception(
            f"Error inesperado en la vista home para el usuario {request.user.username}"
        )
        return render(
            request, "error.html", {"message": "Ha ocurrido un error inesperado"}
        )


@login_required
def login_success(request):
    try:
        cliente = request.user.cliente
        if cliente.is_cliente():
            return redirect("home")
        elif cliente.is_recepcionista():
            return redirect("home")
        else:
            return redirect("error_page")
    except Cliente.DoesNotExist:
        return redirect("error_page")


@login_required
def ver_citas(request):
    citas = (
        Cita.objects.filter(cliente=request.user.cliente)
        .select_related("servicio", "empleado")
        .order_by("fecha", "hora_inicio")
    )
    return render(request, "ver_citas.html", {"citas": citas})


def es_recepcionista(user):
    try:
        return user.cliente.is_recepcionista()
    except Cliente.DoesNotExist:
        return False


def es_cliente(user):
    try:
        return user.cliente.is_cliente()
    except Cliente.DoesNotExist:
        return False


@login_required
@recepcionista_required
def resumen_recepcionista(request):
    try:
        now = timezone.localtime(timezone.now())
        hoy = now.date()
        ahora = now.time()

        citas_hoy = Cita.objects.filter(fecha=hoy).count()
        proxima_cita = (
            Cita.objects.filter(
                fecha=hoy, hora_inicio__gte=ahora, estado=Cita.ESTADO_CONFIRMADA
            )
            .select_related("cliente", "servicio")
            .order_by("hora_inicio")
            .first()
        )

        data = {"citas_hoy": citas_hoy, "proxima_cita": None}

        if proxima_cita:
            data["proxima_cita"] = {
                "cliente": proxima_cita.cliente.nombre,
                "servicio": proxima_cita.servicio.nombre,
                "hora": proxima_cita.hora_inicio.strftime("%H:%M"),
            }
        print("Data enviada:", data)
        return JsonResponse(data)
    except Exception as e:
        print(f"Error en resumen_recepcionista: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


def get_current_time(request):
    current_time = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    return JsonResponse({"current_time": current_time})


def format_currency(value):
    if value is None:
        return "$0.00"
    return f"${value:.2f}"


@login_required
@recepcionista_required
def estadisticas(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if not fecha_inicio:
        fecha_inicio = (timezone.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = timezone.now().strftime("%Y-%m-%d")

    fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

    # Filtro base para las citas
    citas_filter = Q(citas__fecha__range=[fecha_inicio, fecha_fin])

    # Top clientes
    top_clientes = Cliente.objects.annotate(
        num_citas=Count("citas", filter=citas_filter),
    ).order_by("-num_citas")[:10]

    # Top servicios
    servicios_filter = Q(cita__fecha__range=[fecha_inicio, fecha_fin])
    top_servicios = Servicio.objects.annotate(
        num_citas=Count("cita", filter=servicios_filter),
    ).order_by("-num_citas")[:10]

    # Top empleados
    empleados_filter = Q(empleados__fecha__range=[fecha_inicio, fecha_fin])
    top_empleados = Empleado.objects.annotate(
        num_citas=Count("empleados", filter=empleados_filter),
    ).order_by("-num_citas")[:10]

    context = {
        "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_fin": fecha_fin.strftime("%Y-%m-%d"),
        "top_clientes": [
            {
                "nombre": cliente.nombre,
                "num_citas": cliente.num_citas,
            }
            for cliente in top_clientes
        ],
        "top_servicios": [
            {
                "nombre": servicio.nombre,
                "num_citas": servicio.num_citas,
            }
            for servicio in top_servicios
        ],
        "top_empleados": [
            {
                "nombre": empleado.nombre,
                "num_citas": empleado.num_citas,
            }
            for empleado in top_empleados
        ],
    }

    return render(request, "estadisticas.html", context)


@login_required
@recepcionista_required
def estadisticas_pdf(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    # Verificar que las fechas no sean nulas
    if not fecha_inicio or not fecha_fin:
        messages.error(request, "Por favor, seleccione un rango de fechas válido.")
        return redirect("estadisticas")

    try:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        messages.error(request, "Formato de fecha inválido.")
        return redirect("estadisticas")

    # Estadísticas generales
    total_citas = Cita.objects.filter(fecha__range=[fecha_inicio, fecha_fin]).count()
    ingresos_totales = (
        Cita.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin], estado=Cita.ESTADO_TERMINADA
        ).aggregate(total=Sum("servicio__precio"))["total"]
        or 0
    )

    # Servicios
    servicios = Servicio.objects.annotate(
        num_citas=Count("cita", filter=Q(cita__fecha__range=[fecha_inicio, fecha_fin])),
        ingresos=Sum(
            Case(
                When(cita__estado=Cita.ESTADO_TERMINADA, then="precio"),
                default=Value(0),
                output_field=DecimalField(),
            ),
            filter=Q(cita__fecha__range=[fecha_inicio, fecha_fin]),
        ),
    ).order_by("-ingresos")

    # Empleados
    empleados = Empleado.objects.annotate(
        num_citas=Count(
            "empleados", filter=Q(empleados__fecha__range=[fecha_inicio, fecha_fin])
        ),
        ingresos=Sum(
            Case(
                When(
                    empleados__estado=Cita.ESTADO_TERMINADA,
                    then="empleados__servicio__precio",
                ),
                default=Value(0),
                output_field=DecimalField(),
            ),
            filter=Q(empleados__fecha__range=[fecha_inicio, fecha_fin]),
        ),
    ).order_by("-ingresos")

    # Tasa de cancelación
    citas_canceladas = Cita.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin], estado=Cita.ESTADO_CANCELADA
    ).count()
    tasa_cancelacion = (citas_canceladas / total_citas) * 100 if total_citas > 0 else 0

    # Duración promedio de citas
    duracion_promedio = (
        Cita.objects.filter(fecha__range=[fecha_inicio, fecha_fin]).aggregate(
            avg_duration=Avg("servicio__duracion")
        )["avg_duration"]
        or 0
    )

    # Horas pico
    horas_pico = (
        Cita.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        .annotate(hora=ExtractHour("hora_inicio"))
        .values("hora")
        .annotate(count=Count("id"))
        .order_by("-count")[:3]
    )

    context = {
        "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_fin": fecha_fin.strftime("%Y-%m-%d"),
        "total_citas": total_citas,
        "ingresos_totales": format_currency(ingresos_totales),
        "servicios": [
            {
                "nombre": servicio.nombre,
                "num_citas": servicio.num_citas,
                "ingresos": format_currency(servicio.ingresos),
            }
            for servicio in servicios
        ],
        "empleados": [
            {
                "nombre": empleado.nombre,
                "num_citas": empleado.num_citas,
                "ingresos": format_currency(empleado.ingresos),
            }
            for empleado in empleados
        ],
        "tasa_cancelacion": round(tasa_cancelacion, 2),
        "duracion_promedio": round(duracion_promedio),
        "horas_pico": horas_pico,
    }

    return render(request, "estadisticas_pdf.html", context)
