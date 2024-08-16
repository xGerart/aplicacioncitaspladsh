from django.contrib import admin                                                                                                      
from .models import Cliente, Servicio, Empleado, Cita, HorarioEmpleado, AusenciaEmpleado, HorarioCentro
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User



@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'email', 'celular', 'rol')
    list_filter = ('rol',)
    search_fields = ('nombre', 'cedula', 'email')


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion', 'precio', 'duracion')


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cedula', 'nombre', 'email', 'celular')  
    raw_id_fields = ('servicios',)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'servicio', 'empleado', 'fecha', 'hora_inicio', 'estado')
    list_filter = ('servicio', 'empleado', 'estado', 'fecha')
    search_fields = ('cliente__nombre', 'servicio__nombre', 'empleado__nombre')
    date_hierarchy = 'fecha'


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


@admin.register(HorarioCentro)
class HorarioCentroAdmin(admin.ModelAdmin):
    list_display = ('id', 'dia', 'hora_apertura', 'hora_cierre')

class ClienteInline(admin.StackedInline):
    model = Cliente
    can_delete = False
    verbose_name_plural = 'Cliente'

class CustomUserAdmin(UserAdmin):
    inlines = (ClienteInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_rol')

    def get_rol(self, obj):
        try:
            return obj.cliente.get_rol_display()
        except Cliente.DoesNotExist:
            return "No asignado"
    get_rol.short_description = 'Rol'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

