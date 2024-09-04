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
from .models import Empleado, Cita, Cliente, Servicio, HorarioEmpleado, HorarioCentro
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
                messages.success(request, 'Cita agendada con éxito.')
                return redirect('home')
            else:
                messages.error(request, 'Por favor, seleccione una hora para la cita.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CitaForm()
    
    servicios = Servicio.objects.all()
    horario_cierre = HorarioCentro.objects.get(dia=timezone.now().weekday()).hora_cierre
    
    print(f"Fecha actual: {timezone.now().date()}, Hora de cierre: {horario_cierre}")
    
    return render(request, 'cita.html', {
        'form': form, 
        'servicios': servicios,
        'horario_cierre': horario_cierre.strftime('%H:%M')
    })

@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, cliente__user=request.user)
    if cita.es_cancelable():
        cita.estado = Cita.ESTADO_CANCELADA
        cita.save()
        messages.success(request, "Cita cancelada exitosamente")
    else:
        messages.error(request, "No se puede cancelar esta cita")
    return redirect('home')

@login_required
@recepcionista_required
def gestion_citas(request):
    fecha = request.GET.get("fecha")
    if fecha:
        fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    else:
        fecha = timezone.now().date()
    citas = Cita.objects.filter(fecha=fecha).select_related('cliente', 'servicio', 'empleado')
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

from django.utils import timezone
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Empleado, Servicio, Cita, HorarioEmpleado, HorarioCentro

@require_GET
def get_bloques_disponibles(request):
    empleado_id = request.GET.get('empleado')
    servicio_id = request.GET.get('servicio')
    fecha_str = request.GET.get('fecha')
    
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    dia_semana = fecha.weekday()
    
    servicio = get_object_or_404(Servicio, id=servicio_id)
    empleados = [get_object_or_404(Empleado, id=empleado_id)] if empleado_id != '0' else Empleado.objects.filter(servicios__id=servicio_id)
    
    bloques_disponibles = []
    for empleado in empleados:
        horario = empleado.horarios.filter(dia_semana=dia_semana, disponible=True).first()
        if horario:
            hora_actual = horario.hora_inicio
            while hora_actual < horario.hora_fin:
                hora_fin_bloque = (datetime.combine(fecha, hora_actual) + timedelta(minutes=15)).time()
                if hora_fin_bloque <= horario.hora_fin:
                    # Verificar si el bloque está disponible
                    if not Cita.objects.filter(
                        empleado=empleado,
                        fecha=fecha,
                        hora_inicio__lt=hora_fin_bloque,
                        hora_inicio__gte=hora_actual,
                        estado__in=[Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_PROCESO]
                    ).exists():
                        bloques_disponibles.append({
                            'inicio': hora_actual.strftime('%H:%M'),
                            'empleado_id': empleado.id,
                            'empleado_nombre': empleado.nombre
                        })
                hora_actual = hora_fin_bloque

    return JsonResponse({
        'bloques': bloques_disponibles,
        'mensaje': '' if bloques_disponibles else 'No hay horarios disponibles para este día.'
    })
    
@login_required
def home(request):
    try:
        cliente = request.user.cliente
        if cliente.is_cliente():
            citas = Cita.objects.filter(cliente=cliente).order_by('fecha', 'hora_inicio')
            return render(request, 'home.html', {'citas': citas})
        elif cliente.is_recepcionista():
            return render(request, 'home.html')
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
            return redirect('home')
        elif cliente.is_recepcionista():
            return redirect('home')
        else:
            return redirect('error_page')
    except Cliente.DoesNotExist:
        return redirect('error_page')

@login_required
def ver_citas(request):
    citas = Cita.objects.filter(cliente=request.user.cliente).select_related('servicio', 'empleado').order_by('fecha', 'hora_inicio')
    return render(request, 'ver_citas.html', {'citas': citas})

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
    now = timezone.localtime(timezone.now())
    hoy = now.date()
    ahora = now.time()
    
    citas_hoy = Cita.objects.filter(fecha=hoy).count()
    proxima_cita = Cita.objects.filter(
        fecha=hoy,
        hora_inicio__gte=ahora,
        estado=Cita.ESTADO_CONFIRMADA
    ).select_related('cliente', 'servicio').order_by('hora_inicio').first()

    data = {
        'citas_hoy': citas_hoy,
        'proxima_cita': None
    }

    if proxima_cita:
        data['proxima_cita'] = {
            'cliente': proxima_cita.cliente.nombre,
            'servicio': proxima_cita.servicio.nombre,
            'hora': proxima_cita.hora_inicio.strftime('%H:%M')
        }

    return JsonResponse(data)


def get_current_time(request):
    current_time = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
    return JsonResponse({'current_time': current_time})