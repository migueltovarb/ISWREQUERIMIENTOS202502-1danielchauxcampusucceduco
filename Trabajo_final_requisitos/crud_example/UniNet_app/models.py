# ============================================================================
# UNINET - MODELOS COMPLETOS
# Cumple con TODAS las historias de usuario
# ============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
import uuid

# ============================================================================
# MODELO: Administrador
# ============================================================================

class Administrador(models.Model):
    """Administrador del sistema - Historia 4 y 5"""
    ROLES = [
        ('admin_general', 'Administrador General'),
        ('admin_academico', 'Administrador Académico'),
        ('admin_financiero', 'Administrador Financiero'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='administrador')
    rol = models.CharField(max_length=20, choices=ROLES, default='admin_academico')
    departamento = models.CharField(max_length=100)
    codigo_empleado = models.CharField(max_length=20, unique=True)
    permisos_especiales = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"
    
    def __str__(self):
        return f"{self.codigo_empleado} - {self.user.get_full_name()}"

# ============================================================================
# MODELO: Profesor
# ============================================================================

class Profesor(models.Model):
    """Profesor - Historia 4 y 5"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profesor')
    codigo_profesor = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=200)
    departamento = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email_institucional = models.EmailField(validators=[EmailValidator()])
    activo = models.BooleanField(default=True)
    fecha_contratacion = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"
    
    def __str__(self):
        return f"{self.codigo_profesor} - {self.user.get_full_name()}"
    
    def tiene_conflicto_horario(self, nuevo_horario):
        """Historia 5: Validar que el profesor no tenga conflicto de horario"""
        horarios_profesor = self.horarios.filter(
            activo=True,
            periodo=nuevo_horario.periodo
        ).exclude(id=nuevo_horario.id if nuevo_horario.id else None)
        
        for horario in horarios_profesor:
            if horario.validar_conflicto(nuevo_horario):
                return True
        return False

# ============================================================================
# MODELO: Periodo
# ============================================================================

class Periodo(models.Model):
    """Periodo Académico"""
    nombre = models.CharField(max_length=50, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_inicio_inscripciones = models.DateField()
    fecha_fin_inscripciones = models.DateField()
    activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Periodo Académico"
        verbose_name_plural = "Periodos Académicos"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return self.nombre
    
    def esta_vigente(self):
        hoy = timezone.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin and self.activo
    
    def permite_inscripciones(self):
        hoy = timezone.now().date()
        return (self.fecha_inicio_inscripciones <= hoy <= self.fecha_fin_inscripciones 
                and self.activo)

# ============================================================================
# MODELO: Curso
# ============================================================================

class Curso(models.Model):
    """Curso - Historia 1, 2, 4 y 6"""
    TIPO_CURSO = [
        ('regular', 'Curso Regular'),
        ('extension', 'Curso de Extensión'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    creditos = models.IntegerField(validators=[MinValueValidator(1)])
    cupo_maximo = models.IntegerField(validators=[MinValueValidator(1)])
    tipo = models.CharField(max_length=20, choices=TIPO_CURSO, default='regular')
    costo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    activo = models.BooleanField(default=True)
    requisitos = models.TextField(blank=True)
    syllabus = models.FileField(upload_to='syllabus/', blank=True, null=True)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name='cursos', null=True, blank=True)
    
    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def tiene_estudiantes_inscritos(self):
        """Historia 4: Validar si tiene estudiantes antes de eliminar"""
        return self.horarios.filter(
            inscripciones__estado__in=['confirmada', 'pendiente']
        ).exists()
    
    def clean(self):
        """Historia 4: Validaciones"""
        super().clean()
        if self.tipo == 'extension' and self.costo <= 0:
            raise ValidationError('Los cursos de extensión deben tener un costo mayor a 0.')

# ============================================================================
# MODELO: Horario
# ============================================================================

class Horario(models.Model):
    """Horario - Historia 1, 2, 5"""
    DIAS_SEMANA = [
        ('L', 'Lunes'),
        ('M', 'Martes'),
        ('W', 'Miércoles'),
        ('J', 'Jueves'),
        ('V', 'Viernes'),
        ('S', 'Sábado'),
        ('D', 'Domingo'),
    ]
    
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='horarios')
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.CharField(max_length=1, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    aula = models.CharField(max_length=50)
    cupo_maximo = models.IntegerField(validators=[MinValueValidator(1)])
    cupo_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name='horarios')
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"
        ordering = ['dia_semana', 'hora_inicio']
    
    def __str__(self):
        return f"{self.curso.codigo} - {self.get_dia_semana_display()} {self.hora_inicio.strftime('%H:%M')}-{self.hora_fin.strftime('%H:%M')}"
    
    def validar_conflicto(self, otro_horario):
        """Historia 1 y 5: Validar conflictos de horario"""
        if self.periodo != otro_horario.periodo:
            return False
        if self.dia_semana != otro_horario.dia_semana:
            return False
        
        # Verificar solapamiento de horarios
        return not (self.hora_fin <= otro_horario.hora_inicio or 
                   otro_horario.hora_fin <= self.hora_inicio)
    
    def verificar_cupo_disponible(self):
        """Historia 1 y 2: Verificar cupos disponibles"""
        return self.cupo_actual < self.cupo_maximo
    
    def incrementar_cupo(self):
        """Historia 1: Incrementar cupo al inscribirse"""
        if self.cupo_actual < self.cupo_maximo:
            self.cupo_actual += 1
            self.save(update_fields=['cupo_actual'])
        else:
            raise ValidationError("Este curso ya no tiene cupos disponibles.")
    
    def decrementar_cupo(self):
        """Decrementar cupo al cancelar"""
        if self.cupo_actual > 0:
            self.cupo_actual -= 1
            self.save(update_fields=['cupo_actual'])
    
    def calcular_cupos_restantes(self):
        """Historia 2: Calcular cupos restantes"""
        return self.cupo_maximo - self.cupo_actual
    
    def clean(self):
        """Historia 5: Validaciones al guardar"""
        super().clean()
        
        if self.hora_inicio and self.hora_fin and self.hora_inicio >= self.hora_fin:
            raise ValidationError('La hora de inicio debe ser anterior a la hora de fin.')
        
        # Historia 5: Validar conflicto con profesor
        if self.profesor and self.profesor.tiene_conflicto_horario(self):
            raise ValidationError('Conflicto detectado: el docente ya tiene un curso asignado en este horario.')
        
        # Historia 5: Validar conflicto con aula
        if self.id:
            conflictos_aula = Horario.objects.filter(
                aula=self.aula,
                dia_semana=self.dia_semana,
                periodo=self.periodo,
                activo=True
            ).exclude(id=self.id)
        else:
            conflictos_aula = Horario.objects.filter(
                aula=self.aula,
                dia_semana=self.dia_semana,
                periodo=self.periodo,
                activo=True
            )
        
        for horario in conflictos_aula:
            if self.validar_conflicto(horario):
                raise ValidationError('Conflicto detectado: el aula ya está ocupada en este horario.')

# ============================================================================
# MODELO: Estudiante
# ============================================================================

class Estudiante(models.Model):
    """Estudiante - Historia 1, 2, 3 y 6"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='estudiante')
    matricula = models.CharField(max_length=20, unique=True)
    codigo_estudiante = models.CharField(max_length=20, unique=True)
    carrera = models.CharField(max_length=100)
    semestre = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    creditos_acumulados = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    promedio_general = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    fecha_ingreso = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['matricula']
    
    def __str__(self):
        return f"{self.matricula} - {self.user.get_full_name()}"
    
    def inscribir_curso(self, horario):
        """Historia 1: Inscribir en un curso con todas las validaciones"""
        # Validación 1: Cupos disponibles
        if not horario.verificar_cupo_disponible():
            raise ValidationError("Este curso ya no tiene cupos disponibles.")
        
        # Validación 2: Conflicto de horario
        if self.tiene_conflicto_horario(horario):
            raise ValidationError("No puede inscribirse. El horario se superpone con otro curso que ya registró.")
        
        # Validación 3: Inscripción duplicada
        if Inscripcion.objects.filter(
            estudiante=self,
            horario=horario,
            estado__in=['pendiente', 'confirmada']
        ).exists():
            raise ValidationError("Ya está inscrito en este curso.")
        
        # Crear inscripción
        inscripcion = Inscripcion.objects.create(
            estudiante=self,
            horario=horario,
            estado='pendiente' if horario.curso.tipo == 'extension' else 'confirmada'
        )
        
        # Incrementar cupo
        horario.incrementar_cupo()
        
        return inscripcion
    
    def tiene_conflicto_horario(self, nuevo_horario):
        """Historia 1: Verificar conflictos de horario"""
        inscripciones_actuales = Inscripcion.objects.filter(
            estudiante=self,
            estado__in=['confirmada', 'pendiente'],
            horario__periodo=nuevo_horario.periodo,
            horario__activo=True
        )
        
        for inscripcion in inscripciones_actuales:
            if inscripcion.horario.validar_conflicto(nuevo_horario):
                return True
        return False

# ============================================================================
# MODELO: Inscripcion
# ============================================================================

class Inscripcion(models.Model):
    """Inscripción - Historia 1, 3"""
    ESTADO_INSCRIPCION = [
        ('pendiente', 'Pendiente de Pago'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('retirada', 'Retirada'),
    ]
    
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='inscripciones')
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='inscripciones')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_INSCRIPCION, default='pendiente')
    calificacion = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    asistencia = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        unique_together = [['estudiante', 'horario']]
        ordering = ['-fecha_inscripcion']
    
    def __str__(self):
        return f"{self.estudiante.matricula} - {self.horario.curso.nombre}"
    
    def confirmar(self):
        """Confirmar inscripción"""
        if self.estado == 'pendiente':
            self.estado = 'confirmada'
            self.save()
            self.enviar_confirmacion()
    
    def cancelar(self):
        """Cancelar inscripción"""
        if self.estado in ['pendiente', 'confirmada']:
            self.estado = 'cancelada'
            self.save()
            self.horario.decrementar_cupo()
    
    def enviar_confirmacion(self):
        """Historia 3: Enviar correo de confirmación"""
        try:
            asunto = f"Confirmación de Inscripción - {self.horario.curso.nombre}"
            mensaje = f"""
Hola {self.estudiante.user.get_full_name()},

Tu inscripción al curso {self.horario.curso.nombre} ha sido confirmada exitosamente.

Detalles:
- Código: {self.horario.curso.codigo}
- Horario: {self.horario.get_dia_semana_display()} {self.horario.hora_inicio.strftime('%H:%M')} - {self.horario.hora_fin.strftime('%H:%M')}
- Docente: {self.horario.profesor.user.get_full_name()}
- Aula: {self.horario.aula}
- Fecha de inscripción: {self.fecha_inscripcion.strftime('%d/%m/%Y %H:%M')}

¡Te deseamos mucho éxito!

Universidad
            """
            
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [self.estudiante.user.email],
                fail_silently=False,
            )
            
            # Registrar notificación
            NotificacionEmail.objects.create(
                destinatario=self.estudiante.user.email,
                asunto=asunto,
                cuerpo=mensaje,
                tipo='inscripcion_confirmada',
                estado='enviado',
                fecha_envio=timezone.now()
            )
            
        except Exception as e:
            # Registrar error
            NotificacionEmail.objects.create(
                destinatario=self.estudiante.user.email,
                asunto=asunto,
                cuerpo=mensaje,
                tipo='inscripcion_confirmada',
                estado='fallido',
                intentos_envio=1
            )

# ============================================================================
# MODELO: Pago
# ============================================================================

class Pago(models.Model):
    """Pago - Historia 6"""
    METODO_PAGO = [
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('efectivo', 'Efectivo'),
        ('pse', 'PSE'),
    ]
    
    ESTADO_PAGO = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
    ]
    
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO)
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO, default='pendiente')
    numero_transaccion = models.CharField(max_length=100, unique=True, editable=False)
    comprobante = models.FileField(upload_to='comprobantes/', blank=True, null=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha']
    
    def save(self, *args, **kwargs):
        if not self.numero_transaccion:
            self.numero_transaccion = f"PAG-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Pago {self.numero_transaccion} - ${self.monto}"
    
    def procesar_pago(self):
        """Historia 6: Procesar pago"""
        self.estado = 'procesando'
        self.save()
        
        # Simular procesamiento
        if self.metodo_pago in ['tarjeta', 'pse']:
            self.estado = 'completado'
            self.fecha_confirmacion = timezone.now()
            self.inscripcion.confirmar()
            self.enviar_recibo()
        else:
            self.estado = 'pendiente'
        
        self.save()
        return self.estado == 'completado'
    
    def enviar_recibo(self):
        """Historia 6: Enviar recibo por correo"""
        try:
            asunto = f"Recibo de Pago - {self.inscripcion.horario.curso.nombre}"
            mensaje = f"""
Hola {self.inscripcion.estudiante.user.get_full_name()},

Tu pago ha sido procesado exitosamente.

Detalles del pago:
- Número de transacción: {self.numero_transaccion}
- Monto: ${self.monto}
- Curso: {self.inscripcion.horario.curso.nombre}
- Método de pago: {self.get_metodo_pago_display()}
- Fecha: {self.fecha.strftime('%d/%m/%Y %H:%M')}
- Estado: {self.get_estado_display()}

Universidad
            """
            
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [self.inscripcion.estudiante.user.email],
                fail_silently=False,
            )
        except Exception as e:
            pass

# ============================================================================
# MODELO: NotificacionEmail
# ============================================================================

class NotificacionEmail(models.Model):
    """Historia 3: Notificaciones por email"""
    TIPOS_NOTIFICACION = [
        ('inscripcion_confirmada', 'Inscripción Confirmada'),
        ('inscripcion_cancelada', 'Inscripción Cancelada'),
        ('pago_recibido', 'Pago Recibido'),
        ('recordatorio', 'Recordatorio'),
    ]
    
    ESTADO_ENVIO = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
    ]
    
    destinatario = models.EmailField()
    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()
    tipo = models.CharField(max_length=30, choices=TIPOS_NOTIFICACION)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_ENVIO, default='pendiente')
    intentos_envio = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Notificación por Email"
        verbose_name_plural = "Notificaciones por Email"
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"{self.asunto} - {self.destinatario}"

# ============================================================================
# MODELO: Reporte
# ============================================================================

class Reporte(models.Model):
    """Reportes del sistema"""
    TIPOS_REPORTE = [
        ('inscripciones', 'Reporte de Inscripciones'),
        ('pagos', 'Reporte de Pagos'),
        ('estudiantes', 'Reporte de Estudiantes'),
        ('cursos', 'Reporte de Cursos'),
    ]
    
    FORMATOS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPOS_REPORTE)
    formato = models.CharField(max_length=10, choices=FORMATOS, default='pdf')
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    generado_por = models.ForeignKey(Administrador, on_delete=models.CASCADE, related_name='reportes')
    datos = models.JSONField(blank=True, null=True)
    archivo = models.FileField(upload_to='reportes/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"

# ============================================================================
# MODELO: PasarelaPago
# ============================================================================

class PasarelaPago(models.Model):
    """Historia 6: Pasarela de pago"""
    PROVEEDORES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('mercadopago', 'Mercado Pago'),
        ('payu', 'PayU'),
    ]
    
    proveedor = models.CharField(max_length=20, choices=PROVEEDORES, unique=True)
    api_key = models.CharField(max_length=200)
    api_secret = models.CharField(max_length=200)
    url_callback = models.URLField()
    activo = models.BooleanField(default=True)
    configuracion_adicional = models.JSONField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Pasarela de Pago"
        verbose_name_plural = "Pasarelas de Pago"
    
    def __str__(self):
        return self.get_proveedor_display()