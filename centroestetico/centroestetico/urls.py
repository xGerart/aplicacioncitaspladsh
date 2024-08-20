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
from citas import views as citas_views
from . import views as main_views

urlpatterns = [
    path('', main_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('login-success/', citas_views.login_success, name='login_success'),
    path('home-cliente/', citas_views.home_cliente, name='home_cliente'),
    path('home-recepcionista/', citas_views.home_recepcionista, name='home_recepcionista'),
    
    path('citas/', include([
        path('agendar/', citas_views.agendar_cita, name='agendar_cita'),
        path('get_empleados_disponibles/', citas_views.get_empleados_disponibles, name='get_empleados_disponibles'),
        path('get_bloques_disponibles/', citas_views.get_bloques_disponibles, name='get_bloques_disponibles'),
        path('gestion_citas/', citas_views.gestion_citas, name='gestion_citas'),
        path('cancelar/<int:cita_id>/', citas_views.cancelar_cita, name='cancelar_cita'),
    ])),
]