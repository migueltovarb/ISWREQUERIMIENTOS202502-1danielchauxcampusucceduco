# apps/materiales/models.py

from apps.certificados.models import Certificado
from apps.evaluaciones.models import Evaluacion
from apps.core.models import Taller
from django.db import models


class Material(models.Model):
    TIPOS = [
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('enlace', 'Enlace'),
        ('presentacion', 'Presentación'),
        ('otro', 'Otro'),
    ]
    
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name='materiales')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    archivo = models.FileField(upload_to='materiales/', blank=True)
    enlace = models.URLField(blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'materiales'
        ordering = ['-fecha_subida']

class Material(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    certificado = models.ForeignKey(Certificado, on_delete=models.CASCADE)

    class Meta:
        db_table = 'materiales'

class DescargarMaterial(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    fecha_descarga = models.DateTimeField(auto_now_add=True)