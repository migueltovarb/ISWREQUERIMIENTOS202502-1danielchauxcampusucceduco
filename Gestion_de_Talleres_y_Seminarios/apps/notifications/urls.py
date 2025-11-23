from django.urls import path

from apps.certificados import views

urlpatterns = [
    path('', views.index, name='inscripciones_index'),
]
