from django.contrib import admin
from django.urls import path, include
from citas import views as citas_views
from . import views as main_views
from django.conf import settings
from django.conf.urls.static import static

BASE_URL = "https://gerart674.pythonanywhere.com/"

urlpatterns = [
    
    path('', main_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('login-success/', citas_views.login_success, name='login_success'),
    path('ver-citas/', citas_views.ver_citas, name='ver_citas'),
    
    path('citas/', include([
        path('agendar/', citas_views.agendar_cita, name='agendar_cita'),
        path('get_empleados_disponibles/', citas_views.get_empleados_disponibles, name='get_empleados_disponibles'),
        path('get_bloques_disponibles/', citas_views.get_bloques_disponibles, name='get_bloques_disponibles'),
        path('gestion_citas/', citas_views.gestion_citas, name='gestion_citas'),
        path('cancelar/<int:cita_id>/', citas_views.cancelar_cita, name='cancelar_cita'),
        path('resumen_recepcionista/', citas_views.resumen_recepcionista, name='resumen_recepcionista'),
        path('estadisticas/', citas_views.estadisticas, name='estadisticas'),
        path('estadisticas_pdf/', citas_views.estadisticas_pdf, name='estadisticas_pdf'),
    ])),
    path('get_current_time/', citas_views.get_current_time, name='get_current_time'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)