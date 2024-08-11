from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Cliente, Empleado, Servicio
import json

## CLIENTES ##

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


## EMPLEADOS ##

def obtener_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    data = {
        "id": empleado.id,
        "cedula": empleado.cedula,
        "nombre": empleado.nombre,
        "email": empleado.email,
        "celular": empleado.celular,
        "servicios": list(empleado.servicios.values_list("id", flat=True)),
    }
    return JsonResponse(data)


def gestion_empleados(request):
    empleados = Empleado.objects.all()
    servicios = Servicio.objects.all()
    return render(
        request,
        "gestion_empleados.html",
        {"empleados": empleados, "servicios": servicios},
    )


@csrf_exempt
def crear_actualizar_empleado(request):
    if request.method == "POST":
        data = json.loads(request.body)
        empleado_id = data.get("id")

        if empleado_id:
            empleado = get_object_or_404(Empleado, id=empleado_id)
        else:
            empleado = Empleado()

        empleado.cedula = data.get("cedula")
        empleado.nombre = data.get("nombre")
        empleado.email = data.get("email")
        empleado.celular = data.get("celular")

        try:
            empleado.save()
            servicios_ids = data.get("servicios", [])
            empleado.servicios.set(servicios_ids)
            return JsonResponse(
                {"status": "success", "message": "Empleado guardado exitosamente"}
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


@csrf_exempt
def eliminar_empleado(request):
    if request.method == "POST":
        data = json.loads(request.body)
        empleado_id = data.get("id")

        empleado = get_object_or_404(Empleado, id=empleado_id)
        try:
            empleado.delete()
            return JsonResponse(
                {"status": "success", "message": "Empleado eliminado exitosamente"}
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


## SERVICIOS ##

def gestion_servicios(request):
    servicios = Servicio.objects.all()
    return render(request, "gestion_servicios.html", {"servicios": servicios})


@csrf_exempt
def crear_actualizar_servicio(request):
    if request.method == "POST":
        data = json.loads(request.body)
        servicio_id = data.get("id")

        if servicio_id:
            servicio = get_object_or_404(Servicio, id=servicio_id)
        else:
            servicio = Servicio()

        servicio.nombre = data.get("nombre")
        servicio.descripcion = data.get("descripcion")
        servicio.precio = data.get("precio")
        servicio.duracion = data.get("duracion")

        try:
            servicio.save()
            return JsonResponse(
                {"status": "success", "message": "Servicio guardado exitosamente"}
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


@csrf_exempt
def eliminar_servicio(request):
    if request.method == "POST":
        data = json.loads(request.body)
        servicio_id = data.get("id")

        servicio = get_object_or_404(Servicio, id=servicio_id)
        try:
            servicio.delete()
            return JsonResponse(
                {"status": "success", "message": "Servicio eliminado exitosamente"}
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
