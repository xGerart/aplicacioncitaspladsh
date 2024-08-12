from django.urls import path
from . import views

urlpatterns = [
    path('gestion_clientes/', views.gestion_clientes, name='gestion_clientes'),
    path('crear_actualizar_cliente/', views.crear_actualizar_cliente, name='crear_actualizar_cliente'),
    path('eliminar_cliente/', views.eliminar_cliente, name='eliminar_cliente'),
    path('obtener_empleado/<int:empleado_id>/', views.obtener_empleado, name='obtener_empleado'),
    
    path('agendar/', views.agendar_cita, name='agendar_cita'),
]