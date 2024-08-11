from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Cliente, Empleado, Servicio
import json

## CLIENTES ##

# Vista para mostrar todos los clientes en una página HTML
def gestion_clientes(request):
    clientes = Cliente.objects.all()  # Obtiene todos los clientes
    return render(request, 'gestion_clientes.html', {'clientes': clientes})  # Renderiza la plantilla con los clientes

# Vista para crear o actualizar un cliente
@csrf_exempt  # Excluye esta vista de la protección CSRF
def crear_actualizar_cliente(request):
    if request.method == 'POST':  # Solo responde a solicitudes POST
        data = json.loads(request.body)  # Carga los datos JSON del cuerpo de la solicitud
        cliente_id = data.get('id')  # Obtiene el ID del cliente si existe
        
        if cliente_id:
            cliente = get_object_or_404(Cliente, id=cliente_id)  # Busca el cliente por ID o retorna 404 si no se encuentra
        else:
            cliente = Cliente()  # Crea un nuevo objeto Cliente si no se proporciona ID
        
        # Asigna los valores del JSON al objeto cliente
        cliente.cedula = data.get('cedula')
        cliente.nombre = data.get('nombre')
        cliente.email = data.get('email')
        cliente.celular = data.get('celular')
        cliente.fechanacimiento = data.get('fechanacimiento')
        
        try:
            cliente.save()  # Guarda el cliente en la base de datos
            return JsonResponse({'status': 'success', 'message': 'Cliente guardado exitosamente'})  # Respuesta exitosa
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})  # Respuesta con error en caso de excepción

# Vista para eliminar un cliente
@csrf_exempt  # Excluye esta vista de la protección CSRF
def eliminar_cliente(request):
    if request.method == 'POST':  # Solo responde a solicitudes POST
        data = json.loads(request.body)  # Carga los datos JSON del cuerpo de la solicitud
        cliente_id = data.get('id')  # Obtiene el ID del cliente
        
        cliente = get_object_or_404(Cliente, id=cliente_id)  # Busca el cliente por ID o retorna 404 si no se encuentra
        cliente.delete()  # Elimina el cliente de la base de datos
        
        return JsonResponse({'status': 'success', 'message': 'Cliente eliminado exitosamente'})  # Respuesta exitosa

## EMPLEADOS ##

# Vista para obtener detalles de un empleado específico en formato JSON
def obtener_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)  # Busca el empleado por ID o retorna 404 si no se encuentra
    data = {
        'id': empleado.id,
        'cedula': empleado.cedula,
        'nombre': empleado.nombre,
        'email': empleado.email,
        'celular': empleado.celular,
        'servicios': list(empleado.servicios.values_list('id', flat=True))  # Obtiene una lista de IDs de los servicios asociados al empleado
    }
    return JsonResponse(data)  # Devuelve la información del empleado en formato JSON

# Vista para mostrar todos los empleados y servicios en una página HTML
def gestion_empleados(request):
    empleados = Empleado.objects.all()  # Obtiene todos los empleados
    servicios = Servicio.objects.all()  # Obtiene todos los servicios
    return render(request, 'gestion_empleados.html', {'empleados': empleados, 'servicios': servicios})  # Renderiza la plantilla con empleados y servicios

# Vista para crear o actualizar un empleado
@csrf_exempt  # Excluye esta vista de la protección CSRF
def crear_actualizar_empleado(request):
    if request.method == 'POST':  # Solo responde a solicitudes POST
        data = json.loads(request.body)  # Carga los datos JSON del cuerpo de la solicitud
        empleado_id = data.get('id')  # Obtiene el ID del empleado si existe
        
        if empleado_id:
            empleado = get_object_or_404(Empleado, id=empleado_id)  # Busca el empleado por ID o retorna 404 si no se encuentra
        else:
            empleado = Empleado()  # Crea un nuevo objeto Empleado si no se proporciona ID
        
        # Asigna los valores del JSON al objeto empleado
        empleado.cedula = data.get('cedula')
        empleado.nombre = data.get('nombre')
        empleado.email = data.get('email')
        empleado.celular = data.get('celular')
        
        try:
            empleado.save()  # Guarda el empleado en la base de datos
            servicios_ids = data.get('servicios', [])  # Obtiene los IDs de los servicios asociados
            empleado.servicios.set(servicios_ids)  # Asocia los servicios al empleado
            return JsonResponse({'status': 'success', 'message': 'Empleado guardado exitosamente'})  # Respuesta exitosa
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})  # Respuesta con error en caso de excepción

# Vista para eliminar un empleado
@csrf_exempt  # Excluye esta vista de la protección CSRF
def eliminar_empleado(request):
    if request.method == 'POST':  # Solo responde a solicitudes POST
        data = json.loads(request.body)  # Carga los datos JSON del cuerpo de la solicitud
        empleado_id = data.get('id')  # Obtiene el ID del empleado
        
        empleado = get_object_or_404(Empleado, id=empleado_id)  # Busca el empleado por ID o retorna 404 si no se encuentra
        try:
            empleado.delete()  # Elimina el empleado de la base de datos
            return JsonResponse({'status': 'success', 'message': 'Empleado eliminado exitosamente'})  # Respuesta exitosa
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})  # Respuesta con error en caso de excepción

## SERVICIOS ##

# Vista para mostrar todos los servicios en una página HTML
def gestion_servicios(request):
    servicios = Servicio.objects.all()  # Obtiene todos los servicios
    return render(request, 'gestion_servicios.html', {'servicios': servicios})  # Renderiza la plantilla con los servicios

# Vista para crear o actualizar un servicio
@csrf_exempt  # Excluye esta vista de la protección CSRF
def crear_actualizar_servicio(request):
    if request.method == 'POST':  # Solo responde a solicitudes POST
        data = json.loads(request.body)  # Carga los datos JSON del cuerpo de la solicitud
        servicio_id = data.get('id')  # Obtiene el ID del servicio si existe
        
        if servicio_id:
            servicio = get_object_or_404(Servicio, id=servicio_id)  # Busca el servicio por ID o retorna 404 si no se encuentra
        else:
            servicio = Servicio()  # Crea un nuevo objeto Servicio si no se proporciona ID
        
        # Asigna los valores del JSON al objeto servicio
        servicio.nombre = data.get('nombre')
        servicio.descripcion = data.get('descripcion')
        servicio.precio = data.get('precio')
        servicio.duracion = data.get('duracion')
        
        try:
            servicio.save()  # Guarda el servicio en la base de datos
            return JsonResponse({'status': 'success', 'message': 'Servicio guardado exitosamente'})  # Respuesta exitosa
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})  # Respuesta con error en caso de excepción

# Vista para eliminar un servicio
@csrf_exempt  # Excluye esta vista de la protección CSRF
def eliminar_servicio(request):
    if request.method == 'POST':  # Solo responde a solicitudes POST
        data = json.loads(request.body)  # Carga los datos JSON del cuerpo de la solicitud
        servicio_id = data.get('id')  # Obtiene el ID del servicio
        
        servicio = get_object_or_404(Servicio, id=servicio_id)  # Busca el servicio por ID o retorna 404 si no se encuentra
        try:
            servicio.delete()  # Elimina el servicio de la base de datos
            return JsonResponse({'status': 'success', 'message': 'Servicio eliminado exitosamente'})  # Respuesta exitosa
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})  # Respuesta con error en caso de excepción
