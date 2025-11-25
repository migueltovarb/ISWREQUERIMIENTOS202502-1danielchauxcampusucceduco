# vehiclesapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # READ: Lista
    path('', views.vehicle_list, name='vehicle_list'),
    
    # CREATE: Añadir
    path('add/', views.vehicle_create, name='vehicle_create'),
    
    # 💥 UPDATE: Editar por ID (pk = Primary Key)
    path('edit/<int:pk>/', views.vehicle_update, name='vehicle_update'), # <--- ¡AÑADE ESTA LÍNEA!
    
    path('delete/<int:pk>/', views.vehicle_delete, name='vehicle_delete'), # <--- ¡AÑADE ESTA LÍNEA!
]