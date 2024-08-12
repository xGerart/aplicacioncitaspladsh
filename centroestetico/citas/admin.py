from django.contrib import admin

from .models import Cliente, Empleado, Servicio, Cita,HorarioEmpleado, AusenciaEmpleado


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


class HorarioEmpleadoInline(admin.TabularInline):
    model = HorarioEmpleado
    extra = 7 

class AusenciaEmpleadoInline(admin.TabularInline):
    model = AusenciaEmpleado
    extra = 1

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    inlines = [HorarioEmpleadoInline, AusenciaEmpleadoInline]
    list_display = (
        'id',
        'cedula',
        'nombre',
        'email',
        'celular',
        'get_servicios',
    )
    filter_horizontal = ('servicios',)

    def get_servicios(self, obj):
        return obj.get_servicios()
    get_servicios.short_description = 'Servicios'


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion', 'precio', 'duracion')


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
    list_filter = (
        'cliente',
        'servicio',
        'empleado',
        'fechahorainicio',
    )