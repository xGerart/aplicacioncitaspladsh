import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import (
    Q,
    Count,
    Sum,
    Avg,
    Case,
    When,
    Value,
    DecimalField,
    F,
    DateField,
)
from django.db.models.functions import TruncMonth, ExtractHour, TruncDate, ExtractWeekDay
from django.views.decorators.http import require_GET
from .models import Empleado, Cita, Cliente, Servicio, HorarioEmpleado, HorarioCentro
from .forms import CitaForm
from .decorators import cliente_required, recepcionista_required
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db import connection

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
    # horario_cierre = HorarioCentro.objects.get(dia=timezone.now().weekday()).hora_cierre

    # print(f"Fecha actual: {timezone.now().date()}, Hora de cierre: {horario_cierre}")

    return render(
        request,
        "cita.html",
        {
            "form": form,
            "servicios": servicios,
            # 'horario_cierre': horario_cierre.strftime('%H:%M')
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

def get_current_time(request):
    current_time = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
    return JsonResponse({"current_time": current_time})

@require_GET
def get_bloques_disponibles(request):
    try:
        empleado_id = request.GET.get("empleado")
        servicio_id = request.GET.get("servicio")
        fecha_str = request.GET.get("fecha")
        hora_actual_str = request.GET.get("hora_actual")

        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hora_actual = timezone.make_aware(datetime.strptime(hora_actual_str, "%Y-%m-%d %H:%M:%S"))
        dia_semana = fecha.weekday()

        servicio = get_object_or_404(Servicio, id=servicio_id)
        duracion_servicio = timedelta(minutes=servicio.duracion)
        
        if empleado_id == "0":
            empleados = Empleado.objects.filter(servicios__id=servicio_id)
        else:
            empleados = [get_object_or_404(Empleado, id=empleado_id)]

        bloques_disponibles = []
        for empleado in empleados:
            horarios = empleado.horarios.filter(dia_semana=dia_semana, disponible=True)
            
            citas_existentes = Cita.objects.filter(
                empleado=empleado,
                fecha=fecha,
                estado__in=[Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_PROCESO]
            ).order_by('hora_inicio')

            for horario in horarios:
                hora_inicio = max(horario.hora_inicio, hora_actual.time()) if fecha == hora_actual.date() else horario.hora_inicio
                hora_actual_bloque = timezone.make_aware(datetime.combine(fecha, hora_inicio))
                hora_fin_horario = timezone.make_aware(datetime.combine(fecha, horario.hora_fin))

                while hora_actual_bloque + duracion_servicio <= hora_fin_horario:
                    hora_fin_bloque = hora_actual_bloque + timedelta(minutes=15)
                    
                    bloque_ocupado = any(
                        timezone.make_aware(datetime.combine(fecha, cita.hora_inicio)) < hora_fin_bloque and
                        hora_actual_bloque < timezone.make_aware(datetime.combine(fecha, cita.hora_inicio)) + timedelta(minutes=cita.servicio.duracion)
                        for cita in citas_existentes
                    )

                    if not bloque_ocupado:
                        bloques_disponibles.append({
                            "inicio": hora_actual_bloque.time().strftime("%H:%M"),
                            "empleado_id": empleado.id,
                            "empleado_nombre": empleado.nombre,
                        })

                    hora_actual_bloque += timedelta(minutes=15)

        bloques_disponibles.sort(key=lambda x: x['inicio'])

        return JsonResponse({
            "bloques": bloques_disponibles,
            "mensaje": "" if bloques_disponibles else "No hay horarios disponibles para este día.",
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"error": f"Error interno del servidor: {str(e)}"}, status=500)


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





def format_currency(value):
    return f"${value:.2f}" if value is not None else "$0.00"


@login_required
@recepcionista_required
def estadisticas(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if not fecha_inicio:
        fecha_inicio = (timezone.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not fecha_fin:
        fecha_fin = timezone.now().strftime("%Y-%m-%d")

    fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    total_citas = Cita.objects.filter(fecha__range=[fecha_inicio, fecha_fin]).count()

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
    try:
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")

        if not fecha_inicio or not fecha_fin:
            return redirect("estadisticas")

        fecha_inicio = timezone.datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fecha_fin = timezone.datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        # Estadísticas generales
        total_citas = Cita.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        ).count()

        # Servicios más populares
        servicios_populares = Servicio.objects.annotate(
            num_citas=Count(
                "cita", filter=Q(cita__fecha__range=[fecha_inicio, fecha_fin])
            )
        ).order_by("-num_citas")[:5]

        # Empleados más ocupados
        empleados_ocupados = Empleado.objects.annotate(
            num_citas=Count(
                "empleados", filter=Q(empleados__fecha__range=[fecha_inicio, fecha_fin])
            )
        ).order_by("-num_citas")[:5]

        # Tasa de cancelación
        citas_canceladas = Cita.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin], estado=Cita.ESTADO_CANCELADA
        ).count()
        tasa_cancelacion = (
            (citas_canceladas / total_citas * 100) if total_citas > 0 else 0
        )

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

        # Ocupación por día
        ocupacion_por_dia = (
            Cita.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
            .values("fecha")
            .annotate(total_citas=Count("id"), total_duracion=Sum("servicio__duracion"))
            .order_by("fecha")
        )

        # Servicios más cancelados
        servicios_cancelados = Servicio.objects.annotate(
            cancelaciones=Count(
                "cita",
                filter=Q(
                    cita__fecha__range=[fecha_inicio, fecha_fin],
                    cita__estado=Cita.ESTADO_CANCELADA,
                ),
            )
        ).order_by("-cancelaciones")[:5]

        context = {
            "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": fecha_fin.strftime("%Y-%m-%d"),
            "total_citas": total_citas,
            "servicios_populares": servicios_populares,
            "empleados_ocupados": empleados_ocupados,
            "tasa_cancelacion": round(tasa_cancelacion, 2),
            "duracion_promedio": round(duracion_promedio),
            "horas_pico": horas_pico,
            "ocupacion_por_dia": ocupacion_por_dia,
            "servicios_cancelados": servicios_cancelados,
        }

        return render(request, "estadisticas_pdf.html", context)

    except Exception as e:
        logger.error(f"Error en estadisticas_pdf: {str(e)}")
        logger.error(f"Query que causó el error: {connection.queries[-1]['sql']}")
        messages.error(
            request,
            "Ocurrió un error al generar las estadísticas. Por favor, inténtelo de nuevo.",
        )
        return redirect("estadisticas")
