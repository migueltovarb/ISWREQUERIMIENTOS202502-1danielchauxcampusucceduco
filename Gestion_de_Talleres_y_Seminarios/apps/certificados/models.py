# apps/certificados/models.py
from apps.certificados.generators import CertificadoGenerator
from apps.evaluaciones import models
from django.db import models

class MiModelo(models.Model):
    evaluacion = models.ForeignKey('evaluaciones.Evaluacion', on_delete=models.CASCADE)

class Certificado(models.Model):
    inscripcion = models.OneToOneField('inscripciones.Inscripcion', on_delete=models.CASCADE)
    codigo = models.CharField(max_length=10, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to='certificados/')
    
    def generar_pdf(self):
        """Genera y guarda el PDF del certificado"""
        generator = CertificadoGenerator(self.inscripcion)
        pdf_buffer, codigo = generator.generar()
        
        self.codigo = codigo
        filename = f'certificado_{codigo}.pdf'
        self.archivo.save(filename, pdf_buffer, save=True)
        
        # Enviar por email
        from notifications.email_service import EmailService
        email_service = EmailService()
        email_service.enviar_certificado(self)