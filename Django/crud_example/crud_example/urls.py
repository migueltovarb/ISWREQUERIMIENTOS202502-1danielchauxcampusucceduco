# crud_example/urls.py (El archivo GRANDE)

from django.contrib import admin
from django.urls import path, include  # 👈 ¡IMPORTA include!

urlpatterns = [
    path('admin/', admin.site.urls),
    # Envía todo el tráfico principal ('') al enrutador de vehiclesapp.
    path('', include('vehiclesapp.urls')), 
]