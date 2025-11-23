# Talleres_y_Seminarios_Gestión/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # URLs de aplicaciones reales
    path('', include('apps.users.urls')),
    path('talleres/', include('apps.talleres.urls')),
    path('inscripciones/', include('apps.inscripciones.urls')),
    path('asistencia/', include('apps.asistencia.urls')),
    path('certificados/', include('apps.certificados.urls')),
    path('evaluaciones/', include('apps.evaluaciones.urls')),
    path('materiales/', include('apps.materiales.urls')),
    path('pagos/', include('apps.pagos.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('videoconferencia/', include('apps.videoconferencia.urls')),
]

# Archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
