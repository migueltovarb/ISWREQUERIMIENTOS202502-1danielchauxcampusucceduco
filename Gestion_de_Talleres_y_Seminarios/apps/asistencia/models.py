# apps/asistencia/models.py

from django.db import models
from apps.inscripciones.models import Inscripcion


class Asistencia(models.Model):
    ESTADOS = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('tarde', 'Tarde'),
    ]
    
    inscripcion = models.ForeignKey(
        Inscripcion, 
        on_delete=models.CASCADE, 
        related_name='asistencias'
    )

    # Referencia diferida para evitar import circular
    sesion = models.ForeignKey(
        'talleres.Sesion',
        on_delete=models.CASCADE
    )

    estado = models.CharField(max_length=20, choices=ESTADOS)
    observaciones = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'asistencias'
        unique_together = ['inscripcion', 'sesion']

    def __str__(self):
        return f"{self.inscripcion} - {self.sesion} ({self.estado})"



