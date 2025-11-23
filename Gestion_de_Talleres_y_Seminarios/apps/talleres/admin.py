# apps/talleres/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Taller, Sesion

@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'instructor', 'fecha_inicio', 'modalidad', 
                    'cupos_display', 'estado_badge']
    list_filter = ['modalidad', 'estado', 'fecha_inicio']
    search_fields = ['titulo', 'instructor__nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'instructor', 'modalidad')
        }),
        ('Fechas y Duración', {
            'fields': ('fecha_inicio', 'fecha_fin', 'duracion_horas')
        }),
        ('Gestión de Cupos', {
            'fields': ('capacidad_maxima', 'capacidad_minima', 'costo'),
            'description': 'Controla los cupos disponibles y el costo del taller'
        }),
        ('Configuración Virtual', {
            'fields': ('zoom_join_url', 'zoom_password'),
            'classes': ('collapse',)
        }),
    )
    
    def cupos_display(self, obj):
        inscritos = obj.inscripciones.filter(estado='confirmada').count()
        porcentaje = (inscritos / obj.capacidad_maxima) * 100
        
        color = 'green' if porcentaje < 70 else 'orange' if porcentaje < 90 else 'red'
        
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color, inscritos, obj.capacidad_maxima
        )
    cupos_display.short_description = 'Cupos (Inscritos/Total)'
    
    def estado_badge(self, obj):
        colores = {
            'publicado': 'green',
            'confirmado': 'blue',
            'cancelado': 'red',
            'finalizado': 'gray'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colores.get(obj.estado, 'gray'),
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    actions = ['confirmar_talleres', 'cancelar_talleres']
    
    def confirmar_talleres(self, request, queryset):
        queryset.update(estado='confirmado')
        self.message_user(request, f"{queryset.count()} talleres confirmados")
    confirmar_talleres.short_description = "Confirmar talleres seleccionados"
    
    def cancelar_talleres(self, request, queryset):
        queryset.update(estado='cancelado')
        # Enviar emails de cancelación
        from notifications.email_service import EmailService
        email_service = EmailService()
        for taller in queryset:
            for inscripcion in taller.inscripciones.all():
                email_service.enviar_notificacion_cancelacion(inscripcion)
        self.message_user(request, f"{queryset.count()} talleres cancelados")
    cancelar_talleres.short_description = "Cancelar talleres seleccionados"