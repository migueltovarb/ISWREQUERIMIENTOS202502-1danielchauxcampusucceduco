# apps/materiales/admin.py
from django.contrib import admin
from .models import Material

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['pdf', 'video', 'enlace', 'presentacion', 'otro']
    list_filter = ['tipo', 'taller']
    search_fields = ['titulo', 'taller__titulo']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Notificar a inscritos sobre nuevo material
        if not change:  # Solo si es nuevo
            from notifications.email_service import EmailService
            email_service = EmailService()
            email_service.enviar_material_nuevo(obj.taller, obj)
    
    def tamaño_archivo(self, obj):
        if obj.archivo:
            size = obj.archivo.size / 1024 / 1024  # MB
            return f"{size:.2f} MB"
        return "-"
    tamaño_archivo.short_description = 'Tamaño'