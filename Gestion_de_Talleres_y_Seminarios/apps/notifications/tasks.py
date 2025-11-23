# apps/notifications/tasks.py
from celery import shared_task

from apps.inscripciones.models import Inscripcion
from .email_service import EmailService
from django.utils import timezone
from datetime import timedelta

@shared_task
def enviar_recordatorios_24h():
    """Tarea programada: enviar recordatorios 24h antes"""
    from inscripciones.models import Inscripcion
    from django.utils import timezone
    from datetime import timedelta
    
    manana = timezone.now() + timedelta(hours=24)
    inscripciones = Inscripcion.objects.filter(
        taller__fecha_inicio__date=manana.date(),
        estado='confirmada'
    )
    
    email_service = EmailService()
    for inscripcion in inscripciones:
        email_service.enviar_recordatorio_24h(inscripcion)

@shared_task
def enviar_recordatorios_1h():
    """Tarea programada: enviar recordatorios 1h antes"""
    # Similar a la anterior pero con 1 hora
    pass

def procesar_recordatorios():
    """Tarea principal que se ejecuta cada hora"""
    ahora = timezone.now()
    
    # Recordatorios 24 horas
    manana = ahora + timedelta(hours=24)
    inscripciones_24h = Inscripcion.objects.filter(
        taller__fecha_inicio__range=[
            manana - timedelta(minutes=30),
            manana + timedelta(minutes=30)
        ],
        estado='confirmada',
        recordatorio_24h_enviado=False
    )
    
    email_service = EmailService()
    for inscripcion in inscripciones_24h:
        email_service.enviar_recordatorio_24h(inscripcion)
        inscripcion.recordatorio_24h_enviado = True
        inscripcion.save()
    
    # Recordatorios 1 hora
    en_1_hora = ahora + timedelta(hours=1)
    inscripciones_1h = Inscripcion.objects.filter(
        taller__fecha_inicio__range=[
            en_1_hora - timedelta(minutes=15),
            en_1_hora + timedelta(minutes=15)
        ],
        estado='confirmada',
        recordatorio_1h_enviado=False
    )
    
    for inscripcion in inscripciones_1h:
        email_service.enviar_recordatorio_1h(inscripcion)
        inscripcion.recordatorio_1h_enviado = True
        inscripcion.save()