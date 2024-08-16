from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, time
from .models import Empleado, Cita, Cliente
from .forms import CitaForm
from django.core.mail import send_mail
from django.conf import settings
from .decorators import cliente_required, recepcionista_required

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
@cliente_required
def agendar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.cliente = request.user.cliente
            cita.save()
            
            subject = 'Confirmación de Cita'
            message = f'Su cita ha sido agendada para el {cita.fecha} a las {cita.hora_inicio} con {cita.empleado.nombre} para el servicio {cita.servicio.nombre}.'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [request.user.email]
            
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            
            messages.success(request, 'Cita agendada con éxito. Se ha enviado un correo de confirmación.')
            return redirect('ver_citas')
    else:
        form = CitaForm()
    return render(request, 'cita.html', {'form': form})

def get_empleados_disponibles(request):
    servicio_id = request.GET.get('servicio')
    empleados = Empleado.objects.filter(servicios__id=servicio_id)
    data = {
        'empleados': [{'id': emp.id, 'nombre': emp.nombre} for emp in empleados]
    }
    return JsonResponse(data)

def get_bloques_disponibles(request):
    empleado_id = request.GET.get('empleado')
    fecha_str = request.GET.get('fecha')
    
    empleado = get_object_or_404(Empleado, id=empleado_id)
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    
    bloques = [
        (time(9, 0), time(9, 30)),
        (time(9, 30), time(10, 0)),
        (time(10, 0), time(10, 30)),
        (time(10, 30), time(11, 0)),
        (time(11, 0), time(11, 30)),
        (time(11, 30), time(12, 0)),
        (time(12, 0), time(12, 30)),
        (time(12, 30), time(13, 0)),
        (time(14, 0), time(14, 30)),
        (time(14, 30), time(15, 0)),
        (time(15, 0), time(15, 30)),
        (time(15, 30), time(16, 0)),
        (time(16, 0), time(16, 30)),
        (time(16, 30), time(17, 0)),
        (time(17, 0), time(17, 30)),
        (time(17, 30), time(18, 0))
    ]
    
    citas_existentes = Cita.objects.filter(empleado=empleado, fecha=fecha)
    bloques_ocupados = [(cita.hora_inicio, cita.hora_fin) for cita in citas_existentes]
    
    bloques_disponibles = [
        {
            'inicio': bloque[0].strftime('%H:%M'),
            'fin': bloque[1].strftime('%H:%M')
        }
        for bloque in bloques
        if not any(bloque[0] < cita[1] and bloque[1] > cita[0] for cita in bloques_ocupados)
    ]
    
    return JsonResponse({'bloques': bloques_disponibles})

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

@login_required
def ver_citas(request):
    cliente = Cliente.objects.get(user=request.user)
    citas = Cita.objects.filter(cliente=cliente).order_by('fecha', 'hora_inicio')
    for cita in citas:
        cita.estado = cita.estado_actual
    return render(request, "cita.html", {"citas": citas})

@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, cliente__user=request.user)
    if cita.estado == Cita.ESTADO_CONFIRMADA:
        cita.estado = Cita.ESTADO_CANCELADA
        cita.save()
        messages.success(request, "Cita cancelada exitosamente")
    else:
        messages.error(request, "No se puede cancelar esta cita")
    return redirect('ver_citas')

@login_required
def home(request):
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        cliente = Cliente.objects.create(user=request.user, rol=Cliente.CLIENTE, 
                                         nombre=request.user.username, 
                                         email=request.user.email,
                                         cedula='0000000000', 
                                         fechanacimiento=timezone.now().date()) 
    
    is_cliente = cliente.is_cliente()
    is_recepcionista = cliente.is_recepcionista()
    
    context = {
        'is_cliente': is_cliente,
        'is_recepcionista': is_recepcionista,
    }
    
    return render(request, 'home.html', context)
