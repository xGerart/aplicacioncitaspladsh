from django.urls import path
from . import views

urlpatterns = [
    path('gestion_clientes/', views.gestion_clientes, name='gestion_clientes'),
    path('crear_actualizar_cliente/', views.crear_actualizar_cliente, name='crear_actualizar_cliente'),
    path('eliminar_cliente/', views.eliminar_cliente, name='eliminar_cliente'),
    path('obtener_empleado/<int:empleado_id>/', views.obtener_empleado, name='obtener_empleado'),

    path('gestion_empleados/', views.gestion_empleados, name='gestion_empleados'),
    path('crear_actualizar_empleado/', views.crear_actualizar_empleado, name='crear_actualizar_empleado'),
    path('eliminar_empleado/', views.eliminar_empleado, name='eliminar_empleado'),
    path('obtener_empleado/<int:empleado_id>/', views.obtener_empleado, name='obtener_empleado'),

    path('gestion_servicios/', views.gestion_servicios, name='gestion_servicios'),
    path('crear_actualizar_servicio/', views.crear_actualizar_servicio, name='crear_actualizar_servicio'),
    path('eliminar_servicio/', views.eliminar_servicio, name='eliminar_servicio'),
]