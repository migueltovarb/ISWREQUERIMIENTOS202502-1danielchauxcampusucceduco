# apps/talleres/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import Usuario

class Taller(models.Model):
    MODALIDAD_CHOICES = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('hibrida', 'Híbrida'),
    ]
    
    titulo = models.CharField(max_length=200)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    
    # Para talleres virtuales
    zoom_meeting_id = models.CharField(max_length=100, blank=True, null=True)
    zoom_join_url = models.URLField(blank=True, null=True)
    zoom_start_url = models.URLField(blank=True, null=True)
    zoom_password = models.CharField(max_length=50, blank=True, null=True)
    
    def generar_enlace_zoom(self):
        """Genera enlace de Zoom automáticamente para talleres virtuales"""
        if self.modalidad in ['virtual', 'hibrida']:
            from videoconferencia.zoom_service import ZoomService
            
            zoom = ZoomService()
            datos_reunion = zoom.crear_reunion(self)
            
            self.zoom_meeting_id = datos_reunion['id']
            self.zoom_join_url = datos_reunion['join_url']
            self.zoom_start_url = datos_reunion['start_url']
            self.zoom_password = datos_reunion['password']
            self.save()

# Signal para crear Zoom automáticamente
@receiver(post_save, sender=Taller)
def crear_zoom_automatico(sender, instance, created, **kwargs):
    if created and instance.modalidad in ['virtual', 'hibrida']:
        instance.generar_enlace_zoom()

# apps/talleres/models.py

class Taller(models.Model):
    MODALIDAD = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('hibrida', 'Híbrida'),
    ]
    
    ESTADO = [
        ('borrador', 'Borrador'),
        ('pendiente_aprobacion', 'Pendiente Aprobación'),
        ('publicado', 'Publicado'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
        ('finalizado', 'Finalizado'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    instructor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True,
                                   related_name='talleres_impartidos')
    modalidad = models.CharField(max_length=20, choices=MODALIDAD)
    
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    duracion_horas = models.IntegerField()
    
    capacidad_maxima = models.IntegerField()
    capacidad_minima = models.IntegerField()
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    ubicacion = models.CharField(max_length=200, blank=True)
    enlace_virtual = models.URLField(blank=True)
    
    # Zoom
    zoom_meeting_id = models.CharField(max_length=100, blank=True)
    zoom_join_url = models.URLField(blank=True)
    zoom_start_url = models.URLField(blank=True)
    zoom_password = models.CharField(max_length=50, blank=True)
    
    estado = models.CharField(max_length=30, choices=ESTADO, default='borrador')
    publico_objetivo = models.CharField(max_length=100)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'talleres'
        ordering = ['fecha_inicio']
    
    @property
    def cupos_disponibles(self):
        inscritos = self.inscripciones.filter(estado='confirmada').count()
        return self.capacidad_maxima - inscritos
    
    @property
    def alcanza_minimo(self):
        inscritos = self.inscripciones.filter(estado='confirmada').count()
        return inscritos >= self.capacidad_minima

class Sesion(models.Model):
    """Sesiones individuales de un taller"""
    taller = models.ForeignKey(Taller, on_delete=models.CASCADE, related_name='sesiones')
    numero = models.IntegerField()
    fecha = models.DateTimeField()
    tema = models.CharField(max_length=200)
    duracion_minutos = models.IntegerField()
    
    class Meta:
        db_table = 'sesiones'
        ordering = ['numero']
