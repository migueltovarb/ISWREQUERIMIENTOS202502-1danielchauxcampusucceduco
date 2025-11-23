# apps/core/models.py - Modelos base

from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.inscripciones.models import Inscripcion

class Usuario(AbstractUser):
    """Usuario base del sistema"""
    ROLES = [
        ('participante', 'Participante'),
        ('instructor', 'Instructor'),
        ('admin', 'Administrador'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROLES, default='participante')
    documento = models.CharField(max_length=20, unique=True)
    celular = models.CharField(max_length=15)
    programa_academico = models.CharField(max_length=100)
    email_verificado = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usuarios'

class Instructor(models.Model):
    """Información adicional de instructores"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    formacion = models.TextField()
    experiencia = models.TextField()
    foto = models.ImageField(upload_to='instructores/', blank=True)
    temas_especialidad = models.JSONField(default=list)
    
    class Meta:
        db_table = 'instructores'

class Taller(models.Model):
    """Información adicional de talleres"""
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    duracion_horas = models.IntegerField()
    nivel_dificultad = models.CharField(max_length=50)
    requisitos_previos = models.TextField(blank=True)
    
    class Meta:
        db_table = 'talleres'

class Asistencia(models.Model):
    inscripcion = models.ForeignKey(
        'inscripciones.Inscripcion',  # <-- string en lugar de importar
        on_delete=models.CASCADE,
        related_name='asistencias'
    )

