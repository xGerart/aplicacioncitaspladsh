from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers import serialize
from django.http import JsonResponse
from .models import Cliente, Empleado, Servicio
import json

def home(request):
    return render(request, 'home.html')

## CLIENTES ##

@csrf_exempt
def gestion_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, "gestion_clientes.html", {"clientes": clientes})


@csrf_exempt
def crear_actualizar_cliente(request):
    if request.method == "POST":
        data = json.loads(request.body)
        cliente_id = data.get("id")

        if cliente_id:
            cliente = get_object_or_404(Cliente, id=cliente_id)
        else:
            cliente = Cliente()

        cliente.cedula = data.get("cedula")
        cliente.nombre = data.get("nombre")
        cliente.email = data.get("email")
        cliente.celular = data.get("celular")
        cliente.fechanacimiento = data.get("fechanacimiento")

        try:
            cliente.save()
            return JsonResponse(
                {"status": "success", "message": "Cliente guardado exitosamente"}
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


@csrf_exempt
def eliminar_cliente(request):
    if request.method == "POST":
        data = json.loads(request.body)
        cliente_id = data.get("id")

        cliente = get_object_or_404(Cliente, id=cliente_id)
        cliente.delete()

        return JsonResponse(
            {"status": "success", "message": "Cliente eliminado exitosamente"}
        )


## CITAS ##

@csrf_exempt
def agendar_cita(request):
    servicios = Servicio.objects.all()
    empleados = Empleado.objects.all()
    
    servicios_list = json.loads(serialize('json', servicios))
    empleados_list = json.loads(serialize('json', empleados))
    
    for empleado in empleados_list:
        empleado_obj = Empleado.objects.get(pk=empleado['pk'])
        empleado['fields']['servicios'] = list(empleado_obj.servicios.values_list('id', flat=True))
    
    return render(request, 'prototipocitas1.html', {
        'servicios': servicios,  # Pasar los objetos Servicio directamente
        'servicios_json': json.dumps(servicios_list),
        'empleados_json': json.dumps(empleados_list),
    })