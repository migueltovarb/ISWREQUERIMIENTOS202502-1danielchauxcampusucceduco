# apps/users/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@receiver(post_save, sender=User)
def enviar_email_verificacion(sender, instance, created, **kwargs):
    """
    Envía email de verificación cuando se crea un nuevo usuario
    """
    if created and not instance.email_verificado:
        # Generar token de verificación
        token = get_random_string(64)
        
        # Guardar token en el usuario (necesitas agregar campo token_verificacion al modelo)
        instance.token_verificacion = token
        instance.token_verificacion_expira = timezone.now() + timedelta(hours=24)
        instance.save(update_fields=['token_verificacion', 'token_verificacion_expira'])
        
        # Enviar email
        from notifications.email_service import EmailService
        try:
            email_service = EmailService()
            email_service.enviar_email_verificacion(instance, token)
        except Exception as e:
            print(f"Error enviando email de verificación: {e}")


@receiver(pre_save, sender=User)
def validar_email_unico(sender, instance, **kwargs):
    """
    Valida que el email sea único antes de guardar
    """
    if instance.pk:  # Si es actualización
        return
    
    # Verificar email único
    if User.objects.filter(email=instance.email).exists():
        from django.core.exceptions import ValidationError
        raise ValidationError("Este correo electrónico ya está registrado")


@receiver(post_save, sender=User)
def crear_perfil_instructor(sender, instance, created, **kwargs):
    """
    Crea automáticamente un perfil de instructor cuando se registra un usuario con rol instructor
    """
    if created and instance.rol == 'instructor':
        from .models import Instructor
        
        # Verificar si ya tiene perfil
        if not hasattr(instance, 'instructor'):
            Instructor.objects.create(
                usuario=instance,
                formacion="Por completar",
                experiencia="Por completar"
            )


@receiver(post_save, sender=User)
def registrar_actividad_usuario(sender, instance, created, **kwargs):
    """
    Registra la actividad del usuario para analytics
    """
    if created:
        # Log de nuevo registro
        print(f"Nuevo usuario registrado: {instance.email} - Rol: {instance.rol}")
        
        # Aquí podrías agregar lógica para enviar a analytics
        # Por ejemplo, Google Analytics, Mixpanel, etc.


@receiver(post_save, sender=User)
def notificar_administradores_nuevo_instructor(sender, instance, created, **kwargs):
    """
    Notifica a administradores cuando se registra un nuevo instructor
    """
    if created and instance.rol == 'instructor':
        # Obtener emails de administradores
        admins = User.objects.filter(rol='admin', is_active=True)
        admin_emails = [admin.email for admin in admins]
        
        if admin_emails:
            try:
                send_mail(
                    subject='Nuevo instructor registrado',
                    message=f'Un nuevo instructor se ha registrado en el sistema:\n\n'
                            f'Nombre: {instance.get_full_name()}\n'
                            f'Email: {instance.email}\n'
                            f'Documento: {instance.documento}\n'
                            f'Programa: {instance.programa_academico}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True
                )
            except Exception as e:
                print(f"Error notificando a administradores: {e}")


def limpiar_tokens_expirados():
    """
    Función auxiliar para limpiar tokens de verificación expirados
    Debe ejecutarse como tarea programada (Celery)
    """
    usuarios_con_token_expirado = User.objects.filter(
        email_verificado=False,
        token_verificacion_expira__lt=timezone.now()
    )
    
    count = usuarios_con_token_expirado.count()
    
    # Opcional: eliminar usuarios no verificados después de X días
    # usuarios_antiguos = usuarios_con_token_expirado.filter(
    #     date_joined__lt=timezone.now() - timedelta(days=7)
    # )
    # usuarios_antiguos.delete()
    
    return count


def enviar_recordatorio_verificacion():
    """
    Envía recordatorio a usuarios que no han verificado su email
    Debe ejecutarse como tarea programada
    """
    usuarios_sin_verificar = User.objects.filter(
        email_verificado=False,
        date_joined__gte=timezone.now() - timedelta(days=3),
        date_joined__lt=timezone.now() - timedelta(days=2)
    )
    
    from notifications.email_service import EmailService
    email_service = EmailService()
    
    count = 0
    for usuario in usuarios_sin_verificar:
        try:
            email_service.enviar_recordatorio_verificacion(usuario)
            count += 1
        except Exception as e:
            print(f"Error enviando recordatorio a {usuario.email}: {e}")
    
    return count