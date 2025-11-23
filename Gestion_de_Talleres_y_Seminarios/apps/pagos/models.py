# apps/pagos/models.py
from django.db import models
from apps.core.models import Inscripcion

class Pago(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('error', 'Error'),
    ]

    inscripcion = models.OneToOneField(
        Inscripcion, 
        on_delete=models.CASCADE, 
        related_name='pago'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20)  # PSE, CARD, TRANSFER
    estado = models.CharField(max_length=20, choices=ESTADOS)
    referencia_wompi = models.CharField(max_length=100, unique=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    comprobante = models.FileField(upload_to='comprobantes/', null=True, blank=True)

    class Meta:
        db_table = 'pagos'

    def __str__(self):
        return f"Pago {self.referencia_wompi} - {self.estado}"
