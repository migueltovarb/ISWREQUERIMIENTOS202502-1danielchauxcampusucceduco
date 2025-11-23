# apps/notifications/email_service.py
from time import timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from django.conf import settings
from django.template.loader import render_to_string
import base64

class EmailService:
    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
    
    def enviar_confirmacion_inscripcion(self, inscripcion):
        """Envía email de confirmación de inscripción"""
        context = {
            'participante': inscripcion.participante,
            'taller': inscripcion.taller,
            'inscripcion': inscripcion
        }
        
        html_content = render_to_string('emails/confirmacion_inscripcion.html', context)
        
        message = Mail(
            from_email=('noreply@tuuniversidad.edu.co', 'Sistema de Talleres'),
            to_emails=inscripcion.participante.email,
            subject=f'Confirmación de inscripción - {inscripcion.taller.titulo}',
            html_content=html_content
        )
        
        # Adjuntar archivo .ics para calendario
        ics_content = self._generar_ics(inscripcion)
        attachment = Attachment(
            FileContent(base64.b64encode(ics_content.encode()).decode()),
            FileName('evento.ics'),
            FileType('text/calendar'),
            Disposition('attachment')
        )
        message.attachment = attachment
        
        response = self.client.send(message)
        return response.status_code == 202
    
    def enviar_recordatorio_24h(self, inscripcion):
        """Envía recordatorio 24 horas antes"""
        context = {
            'participante': inscripcion.participante,
            'taller': inscripcion.taller,
            'sesion_proxima': inscripcion.taller.sesiones.filter(fecha__gte=timezone.now()).first()
        }
        
        html_content = render_to_string('emails/recordatorio_24h.html', context)
        
        message = Mail(
            from_email=('noreply@tuuniversidad.edu.co', 'Sistema de Talleres'),
            to_emails=inscripcion.participante.email,
            subject=f'Recordatorio: {inscripcion.taller.titulo} mañana',
            html_content=html_content
        )
        
        self.client.send(message)
    
    def enviar_material_nuevo(self, taller, material):
        """Notifica cuando se sube nuevo material"""
        inscritos = taller.inscripciones.filter(estado='confirmada')
        
        for inscripcion in inscritos:
            context = {
                'participante': inscripcion.participante,
                'taller': taller,
                'material': material
            }
            
            html_content = render_to_string('emails/nuevo_material.html', context)
            
            message = Mail(
                from_email=('noreply@tuuniversidad.edu.co', 'Sistema de Talleres'),
                to_emails=inscripcion.participante.email,
                subject=f'Nuevo material disponible - {taller.titulo}',
                html_content=html_content
            )
            
            self.client.send(message)
    
    def enviar_certificado(self, certificado):
        """Envía certificado por email"""
        context = {
            'participante': certificado.inscripcion.participante,
            'taller': certificado.inscripcion.taller,
            'certificado': certificado
        }
        
        html_content = render_to_string('emails/certificado_disponible.html', context)
        
        # Adjuntar PDF del certificado
        with open(certificado.archivo.path, 'rb') as f:
            pdf_content = f.read()
        
        message = Mail(
            from_email=('noreply@tuuniversidad.edu.co', 'Sistema de Talleres'),
            to_emails=certificado.inscripcion.participante.email,
            subject=f'Tu certificado - {certificado.inscripcion.taller.titulo}',
            html_content=html_content
        )
        
        attachment = Attachment(
            FileContent(base64.b64encode(pdf_content).decode()),
            FileName(f'certificado_{certificado.codigo}.pdf'),
            FileType('application/pdf'),
            Disposition('attachment')
        )
        message.attachment = attachment
        
        self.client.send(message)
    
    def _generar_ics(self, inscripcion):
        """Genera archivo .ics para calendario"""
        from calendar import Calendar, Event
        
        cal = Calendar()
        event = Event()
        event.add('summary', inscripcion.taller.titulo)
        event.add('dtstart', inscripcion.taller.fecha_inicio)
        event.add('dtend', inscripcion.taller.fecha_fin)
        event.add('description', inscripcion.taller.descripcion)
        event.add('location', inscripcion.taller.ubicacion or inscripcion.taller.enlace_virtual)
        
        cal.add_component(event)
        return cal.to_ical().decode('utf-8')