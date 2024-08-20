import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import Q
from django.views.decorators.http import require_GET
from .models import Empleado, Cita, Cliente, Servicio, HorarioEmpleado, AusenciaEmpleado
from .forms import CitaForm
from .decorators import cliente_required, recepcionista_required

logger = logging.getLogger(__name__)

@login_required
@cliente_required
def agendar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.cliente = request.user.cliente
            cita.servicio_id = request.POST.get('servicio_id')
            cita.estado = Cita.ESTADO_CONFIRMADA
           
            if cita.hora_inicio:
                cita.save()
                send_mail(
                    'Confirmación de cita',
                    f'Su cita ha sido agendada para el {cita.fecha} a las {cita.hora_inicio}.',
                    'noreply@gerart674.pythonanywhere.com',
                    [request.user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Cita agendada con éxito. Se ha enviado un correo de confirmación.')
                return redirect('home_cliente')
            else:
                messages.error(request, 'Por favor, seleccione una hora para la cita.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CitaForm()
    
    servicios = Servicio.objects.all()
    return render(request, 'cita.html', {'form': form, 'servicios': servicios})

@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, cliente__user=request.user)
    if cita.es_cancelable():
        cita.estado = Cita.ESTADO_CANCELADA
        cita.save()
        messages.success(request, "Cita cancelada exitosamente")
    else:
        messages.error(request, "No se puede cancelar esta cita")
    return redirect('home_cliente')

@login_required
@recepcionista_required
def gestion_citas(request):
    fecha = request.GET.get("fecha")
    if fecha:
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    else:
        fecha = timezone.now().date()
    citas = Cita.objects.filter(fecha=fecha)
    for cita in citas:
        cita.estado = cita.estado_actual
    empleados = Empleado.objects.all()
    return render(request, "gestion_citas.html", {"citas": citas, "empleados": empleados, "fecha": fecha})

@require_GET
def get_empleados_disponibles(request):
    servicio_id = request.GET.get('servicio')
    empleados = Empleado.objects.filter(servicios__id=servicio_id)
    cualquier_empleado = Empleado.get_cualquier_empleado()
    data = {
        'empleados': [{'id': emp.id, 'nombre': emp.nombre} for emp in [cualquier_empleado] + list(empleados)]
    }
    return JsonResponse(data)

@require_GET
def get_bloques_disponibles(request):
    empleado_id = request.GET.get('empleado')
    servicio_id = request.GET.get('servicio')
    fecha_str = request.GET.get('fecha')
    
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    dia_semana = fecha.weekday()
    hora_actual = timezone.localtime(timezone.now()).time()
    
    servicio = get_object_or_404(Servicio, id=servicio_id)
    duracion_servicio = timedelta(minutes=servicio.duracion)
    
    empleados = [get_object_or_404(Empleado, id=empleado_id)] if empleado_id != '0' else Empleado.objects.filter(servicios__id=servicio_id)
    
    todos_bloques = []
    for empleado in empleados:
        horario = empleado.horarios.filter(dia_semana=dia_semana).first()
        if horario:
            hora_inicio = datetime.combine(fecha, horario.hora_inicio)
            hora_fin = datetime.combine(fecha, horario.hora_fin)
            
            while hora_inicio + duracion_servicio <= hora_fin:
                todos_bloques.append((hora_inicio.time(), (hora_inicio + duracion_servicio).time(), empleado))
                hora_inicio += timedelta(minutes=30)

    citas_existentes = Cita.objects.filter(
        Q(empleado__in=empleados) | Q(empleado__isnull=True),
        fecha=fecha,
        estado__in=[Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_PROCESO]
    )
    
    ausencias = AusenciaEmpleado.objects.filter(
        empleado__in=empleados,
        fecha_inicio__date__lte=fecha,
        fecha_fin__date__gte=fecha
    )
    
    bloques_disponibles = [
        {
            'inicio': bloque[0].strftime('%H:%M'),
            'fin': bloque[1].strftime('%H:%M'),
            'empleado_id': bloque[2].id,
            'empleado_nombre': bloque[2].nombre
        }
        for bloque in todos_bloques
        if not any(bloque[0] < cita.hora_fin and bloque[1] > cita.hora_inicio for cita in citas_existentes)
        and not any(bloque[0] < ausencia.fecha_fin.time() and bloque[1] > ausencia.fecha_inicio.time() for ausencia in ausencias)
        and (fecha != timezone.localtime(timezone.now()).date() or bloque[0] > hora_actual)
    ]
    
    return JsonResponse({'bloques': bloques_disponibles, 'mensaje': '' if bloques_disponibles else 'No hay horarios disponibles para este día.'})

@login_required
def home(request):
    try:
        cliente = request.user.cliente
        if cliente.is_cliente():
            citas = Cita.objects.filter(cliente=cliente).order_by('fecha', 'hora_inicio')
            return render(request, 'home_cliente.html', {'citas': citas})
        elif cliente.is_recepcionista():
            return render(request, 'home_recepcionista.html')
        else:
            return render(request, 'error.html', {'message': 'Rol de usuario no reconocido'})
    except Cliente.DoesNotExist:
        return render(request, 'error.html', {'message': 'Perfil de usuario no encontrado'})
    except Exception as e:
        logger.exception(f"Error inesperado en la vista home para el usuario {request.user.username}")
        return render(request, 'error.html', {'message': 'Ha ocurrido un error inesperado'})

@login_required
def login_success(request):
    try:
        cliente = request.user.cliente
        if cliente.is_cliente():
            return redirect('home_cliente')
        elif cliente.is_recepcionista():
            return redirect('home_recepcionista')
        else:
            return redirect('error_page')
    except Cliente.DoesNotExist:
        return redirect('error_page')

@login_required
def home_cliente(request):
    citas = Cita.objects.filter(cliente=request.user.cliente).order_by('fecha', 'hora_inicio')
    return render(request, 'home_cliente.html', {'citas': citas})

@login_required
def home_recepcionista(request):
    return render(request, 'home_recepcionista.html')

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