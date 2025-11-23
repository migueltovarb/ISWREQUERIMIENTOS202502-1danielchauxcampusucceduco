# apps/certificados/generators.py
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode
from io import BytesIO
from django.conf import settings
import uuid

from apps.certificados import models

class CertificadoGenerator:
    def __init__(self, inscripcion):
        self.inscripcion = inscripcion
        self.taller = inscripcion.taller
        self.participante = inscripcion.participante
        
    def generar(self):
        """Genera el PDF del certificado"""
        buffer = BytesIO()
        
        # Crear canvas en orientación horizontal
        c = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Fondo decorativo (opcional)
        # c.drawImage('path/to/template.png', 0, 0, width, height)
        
        # Logo institucional
        logo_path = f'{settings.STATIC_ROOT}/images/logo_universidad.png'
        c.drawImage(logo_path, 1*inch, height - 2*inch, width=2*inch, height=1*inch)
        
        # Título
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(width/2, height - 2.5*inch, "CERTIFICADO")
        
        # Subtítulo
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height - 3*inch, "La Universidad certifica que")
        
        # Nombre del participante
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width/2, height - 3.7*inch, self.participante.nombre_completo.upper())
        
        # Texto principal
        c.setFont("Helvetica", 14)
        texto = f"participó exitosamente en el taller"
        c.drawCentredString(width/2, height - 4.3*inch, texto)
        
        # Nombre del taller
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 4.9*inch, self.taller.titulo)
        
        # Detalles
        c.setFont("Helvetica", 12)
        duracion_texto = f"Con una duración de {self.taller.duracion_horas} horas académicas"
        c.drawCentredString(width/2, height - 5.4*inch, duracion_texto)
        
        fecha_texto = f"Realizado el {self.taller.fecha_inicio.strftime('%d de %B de %Y')}"
        c.drawCentredString(width/2, height - 5.8*inch, fecha_texto)
        
        # Generar código único
        codigo = str(uuid.uuid4())[:8].upper()
        
        # QR Code
        qr_data = f"{settings.SITE_URL}/certificados/verificar/{codigo}"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        c.drawImage(ImageReader(qr_buffer), width - 2*inch, 0.5*inch, 
                   width=1.5*inch, height=1.5*inch)
        
        # Código de verificación
        c.setFont("Helvetica", 10)
        c.drawString(width - 2*inch, 0.3*inch, f"Código: {codigo}")
        
        # Firma digital
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(2.5*inch, 1.5*inch, "_" * 30)
        c.setFont("Helvetica", 10)
        c.drawCentredString(2.5*inch, 1.2*inch, "Coordinador Académico")
        c.drawCentredString(2.5*inch, 1*inch, "Universidad XYZ")
        
        # Pie de página
        c.setFont("Helvetica", 8)
        c.drawCentredString(width/2, 0.3*inch, 
                           f"Verificable en: {settings.SITE_URL}/certificados/verificar/")
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer, codigo

