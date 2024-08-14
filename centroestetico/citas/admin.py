from django.contrib import admin

from .models import Cliente, Servicio, Empleado, Cita, HorarioEmpleado, AusenciaEmpleado


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cedula',
        'nombre',
        'email',
        'celular',
        'fechanacimiento',
    )
    list_filter = ('fechanacimiento',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion', 'precio', 'duracion')


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'obtener_servicios')


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cliente',
        'servicio',
        'empleado',
        'fechahorainicio',
        'estado',
        'notas',
    )
    list_filter = ('cliente', 'servicio', 'empleado', 'fechahorainicio')


@admin.register(HorarioEmpleado)
class HorarioEmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'empleado',
        'dia_semana',
        'hora_inicio',
        'hora_fin',
        'disponible',
    )
    list_filter = ('empleado', 'disponible')


@admin.register(AusenciaEmpleado)
class AusenciaEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'empleado', 'fecha_inicio', 'fecha_fin', 'motivo')
    list_filter = ('empleado', 'fecha_inicio', 'fecha_fin')