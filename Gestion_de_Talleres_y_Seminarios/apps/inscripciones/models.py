from django.db import models
from django.conf import settings


class Inscripcion(models.Model):
    ESTADOS = [
        ('pendiente_pago', 'Pendiente de Pago'),    
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]

    from django.db import models
from django.conf import settings

class Inscripcion(models.Model):
    ESTADOS = [
        ('pendiente_pago', 'Pendiente de Pago'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    taller = models.ForeignKey('talleres.Taller', on_delete=models.CASCADE)


    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente_pago')
    porcentaje_asistencia = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    recordatorio_24h_enviado = models.BooleanField(default=False)
    recordatorio_1h_enviado = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.usuario} inscrito en {self.taller}"


class ListaEspera(models.Model):
    taller = models.ForeignKey('talleres.Taller', on_delete=models.CASCADE)
    participante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='activo')

    class Meta:
        db_table = 'lista_espera'
        ordering = ['fecha_registro']

    def __str__(self):
        return f"{self.participante} en lista de espera para {self.taller}"