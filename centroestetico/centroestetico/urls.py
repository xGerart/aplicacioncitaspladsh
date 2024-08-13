"""
URL configuration for centroestetico project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from citas import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('citas/gestion_clientes/', views.gestion_clientes, name='gestion_clientes'),
    path('citas/crear_actualizar_cliente/', views.crear_actualizar_cliente, name='crear_actualizar_cliente'),
    path('citas/eliminar_cliente/', views.eliminar_cliente, name='eliminar_cliente'),
    path('citas/agendar/', views.agendar_cita, name='agendar_cita'),
    path('accounts/', include('allauth.urls')),
]
