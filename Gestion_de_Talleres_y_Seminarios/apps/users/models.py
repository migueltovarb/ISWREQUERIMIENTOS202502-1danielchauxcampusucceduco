# apps/users/models.py
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import Usuario
from django.db import models
from .models import Usuario  # si estás importando tu propio modelo

class ConsentimientoDatos(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    acepta_terminos = models.BooleanField(default=False)
    acepta_tratamiento_datos = models.BooleanField(default=False)
    fecha_aceptacion = models.DateTimeField(auto_now_add=True)
    ip_registro = models.GenericIPAddressField()

    def __str__(self):
        return f"Consentimiento de {self.usuario}"
    
class Usuario(models.Model):
    # Campos personalizados para el usuario
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.username