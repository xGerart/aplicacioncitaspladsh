from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from .models import Cliente, Servicio, Empleado, Cita, HorarioEmpleado, AusenciaEmpleado, HorarioCentro

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'cedula', 'email', 'celular', 'rol_icon')
    list_filter = ('rol',)
    search_fields = ('nombre', 'apellido', 'cedula', 'email')
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'cedula', 'fechanacimiento')
        }),
        ('Contacto', {
            'fields': ('email', 'celular')
        }),
        ('Rol', {
            'fields': ('rol',)
        }),
    )

    def rol_icon(self, obj):
        if obj.rol == Cliente.CLIENTE:
            return format_html('<i class="fas fa-user" style="color: #4a90e2;"></i> Cliente')
        elif obj.rol == Cliente.RECEPCIONISTA:
            return format_html('<i class="fas fa-user-tie" style="color: #28a745;"></i> Recepcionista')
    rol_icon.short_description = 'Rol'

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion_corta', 'precio', 'duracion', 'imagen_preview')
    search_fields = ('nombre',)
    
    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'

    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="50" height="50" />', obj.imagen.url)
        return "Sin imagen"
    imagen_preview.short_description = 'Imagen'

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula', 'email', 'celular', 'servicios_count')
    search_fields = ('nombre', 'cedula', 'email')
    filter_horizontal = ('servicios',)

    def servicios_count(self, obj):
        count = obj.servicios.count()
        return format_html('<span style="color: #4a90e2;">{}</span> servicios', count)
    servicios_count.short_description = 'Servicios'

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'servicio', 'empleado', 'fecha', 'hora_inicio', 'estado_icon')
    list_filter = ('servicio', 'empleado', 'estado', 'fecha')
    search_fields = ('cliente__nombre', 'servicio__nombre', 'empleado__nombre')
    date_hierarchy = 'fecha'
    readonly_fields = ('hora_fin',)

    def estado_icon(self, obj):
        icons = {
            Cita.ESTADO_CANCELADA: '<i class="fas fa-times-circle" style="color: #dc3545;"></i> Cancelada',
            Cita.ESTADO_CONFIRMADA: '<i class="fas fa-check-circle" style="color: #28a745;"></i> Confirmada',
            Cita.ESTADO_EN_PROCESO: '<i class="fas fa-clock" style="color: #ffc107;"></i> En Proceso',
            Cita.ESTADO_TERMINADA: '<i class="fas fa-flag-checkered" style="color: #17a2b8;"></i> Terminada'
        }
        return format_html(icons.get(obj.estado, ''))
    estado_icon.short_description = 'Estado'

@admin.register(HorarioEmpleado)
class HorarioEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'dia_semana', 'hora_inicio', 'hora_fin', 'disponible_icon')
    list_filter = ('empleado', 'dia_semana', 'disponible')

    def disponible_icon(self, obj):
        if obj.disponible:
            return format_html('<i class="fas fa-check" style="color: #28a745;"></i>')
        return format_html('<i class="fas fa-times" style="color: #dc3545;"></i>')
    disponible_icon.short_description = 'Disponible'

@admin.register(AusenciaEmpleado)
class AusenciaEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha_inicio', 'fecha_fin', 'motivo_corto')
    list_filter = ('empleado', 'fecha_inicio', 'fecha_fin')
    search_fields = ('empleado__nombre', 'motivo')

    def motivo_corto(self, obj):
        return obj.motivo[:30] + '...' if len(obj.motivo) > 30 else obj.motivo
    motivo_corto.short_description = 'Motivo'

@admin.register(HorarioCentro)
class HorarioCentroAdmin(admin.ModelAdmin):
    list_display = ('get_dia_display', 'hora_apertura', 'hora_cierre')
    list_filter = ('dia',)

class ClienteInline(admin.StackedInline):
    model = Cliente
    can_delete = False
    verbose_name_plural = 'Cliente'

class CustomUserAdmin(BaseUserAdmin):
    inlines = (ClienteInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_rol')

    def get_rol(self, obj):
        try:
            return obj.cliente.get_rol_display()
        except Cliente.DoesNotExist:
            return "No asignado"
    get_rol.short_description = 'Rol'

# Desregistra User y Group
admin.site.unregister(User)
admin.site.unregister(Group)

# Registra User con CustomUserAdmin
admin.site.register(User, CustomUserAdmin)

