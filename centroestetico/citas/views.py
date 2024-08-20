from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.core.mail import send_mail
from django.conf import settings
from .models import Empleado, Cita, Cliente, Servicio, HorarioEmpleado
from .forms import CitaForm
from .decorators import cliente_required, recepcionista_required
import logging
from django.core.exceptions import PermissionDenied
from django.db.models import Q

# Vistas relacionadas con Citas
@login_required
@cliente_required
def agendar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.cliente = request.user.cliente
            cita.servicio_id = request.POST.get('servicio_id')
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
    if cita.estado == Cita.ESTADO_CONFIRMADA:
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
        citas = Cita.objects.filter(fecha=fecha)
    else:
        fecha = timezone.now().date()
        citas = Cita.objects.filter(fecha=fecha)

    for cita in citas:
        cita.estado = cita.estado_actual

    empleados = Empleado.objects.all()
    return render(
        request,
        "gestion_citas.html",
        {"citas": citas, "empleados": empleados, "fecha": fecha},
    )

# Vistas relacionadas con Empleados
def get_empleados_disponibles(request):
    servicio_id = request.GET.get('servicio')
    empleados = Empleado.objects.filter(servicios__id=servicio_id)
    cualquier_empleado = Empleado.get_cualquier_empleado()
    data = {
        'empleados': [{'id': emp.id, 'nombre': emp.nombre} for emp in [cualquier_empleado] + list(empleados)]
    }
    return JsonResponse(data)

def get_bloques_disponibles(request):
    empleado_id = request.GET.get('empleado')
    servicio_id = request.GET.get('servicio')
    fecha_str = request.GET.get('fecha')
    
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    dia_semana = fecha.weekday()
    hora_actual = timezone.localtime(timezone.now()).time()
    
    servicio = get_object_or_404(Servicio, id=servicio_id)
    duracion_servicio = timedelta(minutes=servicio.duracion)
    
    if empleado_id == '0':  # significa cualquier profesional
        empleados = Empleado.objects.filter(servicios__id=servicio_id)
    else:
        empleados = [get_object_or_404(Empleado, id=empleado_id)]
    
    todos_bloques = []
    for empleado in empleados:
        horario = HorarioEmpleado.objects.filter(empleado=empleado, dia_semana=dia_semana, disponible=True).first()
        if horario:
            hora_inicio = datetime.combine(fecha, horario.hora_inicio)
            hora_fin = datetime.combine(fecha, horario.hora_fin)
            
            while hora_inicio + duracion_servicio <= hora_fin:
                todos_bloques.append((hora_inicio.time(), (hora_inicio + duracion_servicio).time(), empleado))
                hora_inicio += timedelta(minutes=30)
    
    # obtengo todas las citas existentes para ese día y empleados
    citas_existentes = Cita.objects.filter(
        Q(empleado__in=empleados) | Q(empleado__isnull=True),
        fecha=fecha
    )
    bloques_ocupados = [(cita.hora_inicio, cita.hora_fin) for cita in citas_existentes]
    
    # filtro los bloques disponibles
    bloques_disponibles = [
        {
            'inicio': bloque[0].strftime('%H:%M'),
            'fin': bloque[1].strftime('%H:%M'),
            'empleado_id': bloque[2].id,
            'empleado_nombre': bloque[2].nombre
        }
        for bloque in todos_bloques
        if not any(bloque[0] < cita[1] and bloque[1] > cita[0] for cita in bloques_ocupados)
        and (fecha != timezone.localtime(timezone.now()).date() or bloque[0] > hora_actual)
    ]
    
    if not bloques_disponibles:
        return JsonResponse({'bloques': [], 'mensaje': 'No hay horarios disponibles para este día.'})
    
    return JsonResponse({'bloques': bloques_disponibles, 'mensaje': ''})

def generar_bloques(hora_inicio, hora_fin, duracion):
    bloques = []
    hora_actual = hora_inicio
    while hora_actual + duracion <= hora_fin:
        hora_fin_bloque = (datetime.combine(date.today(), hora_actual) + duracion).time()
        bloques.append((hora_actual, hora_fin_bloque))
        hora_actual = (datetime.combine(date.today(), hora_actual) + timedelta(minutes=30)).time()
    return bloques

# Vista principal
logger = logging.getLogger(__name__)

@login_required
def home(request):
    logger.info(f"Usuario {request.user.username} accediendo a la vista home")
    try:
        cliente = request.user.cliente
        logger.info(f"Cliente encontrado: {cliente.nombre}, Rol: {cliente.rol}")
        
        if cliente.is_cliente():
            logger.info(f"Usuario {request.user.username} identificado como cliente")
            citas = Cita.objects.filter(cliente=cliente).order_by('fecha', 'hora_inicio')
            logger.info(f"Número de citas encontradas: {citas.count()}")
            return render(request, 'home_cliente.html', {'citas': citas})
        elif cliente.is_recepcionista():
            logger.info(f"Usuario {request.user.username} identificado como recepcionista")
            return render(request, 'home_recepcionista.html')
        else:
            logger.warning(f"Usuario {request.user.username} tiene un rol no reconocido: {cliente.rol}")
            return render(request, 'error.html', {'message': 'Rol de usuario no reconocido'})
    except Cliente.DoesNotExist:
        logger.error(f"No se encontró perfil de Cliente para el usuario {request.user.username}")
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

# Funciones auxiliares
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