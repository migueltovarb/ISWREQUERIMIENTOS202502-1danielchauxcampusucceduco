# apps/administracion/views.py
from django.utils import timezone
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count, Avg, Q, F
from apps.core.models import Usuario
from apps.inscripciones.models import Inscripcion, ListaEspera
from apps.materiales.models import Material
from apps.talleres.models import Taller
from apps.evaluaciones.models import Evaluacion

@staff_member_required
def dashboard_admin(request):
    """Dashboard personalizado para administradores"""
    
    # Estadísticas generales
    stats = {
        'talleres_activos': Taller.objects.filter(estado='publicado').count(),
        'total_inscritos': Inscripcion.objects.filter(estado='confirmada').count(),
        'talleres_pendientes': Taller.objects.filter(estado='pendiente_aprobacion').count(),
        'evaluacion_promedio': Evaluacion.objects.aggregate(Avg('satisfaccion_general'))['satisfaccion_general__avg']
    }
    
    # Talleres con bajo cupo
    talleres_bajo_cupo = Taller.objects.annotate(
        num_inscritos=Count('inscripciones', filter=Q(inscripciones__estado='confirmada'))
    ).filter(
        num_inscritos__lt=F('capacidad_minima'),
        fecha_inicio__gte=timezone.now()
    )
    
    # Materiales recientes
    materiales_recientes = Material.objects.order_by('-fecha_subida')[:10]
    
    context = {
        'stats': stats,
        'talleres_bajo_cupo': talleres_bajo_cupo,
        'materiales_recientes': materiales_recientes,
    }
    
    return render(request, 'administracion/dashboard.html', context)

@staff_member_required
def gestionar_cupos(request, taller_id):
    """Vista para gestionar cupos de un taller específico"""
    taller = get_object_or_404(Taller, id=taller_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'aumentar_capacidad':
            nueva_capacidad = int(request.POST.get('nueva_capacidad'))
            taller.capacidad_maxima = nueva_capacidad
            taller.save()
            
            # Notificar a personas en lista de espera
            lista_espera = ListaEspera.objects.filter(taller=taller, estado='activo')
            cupos_liberados = nueva_capacidad - taller.inscripciones.filter(estado='confirmada').count()
            
            for persona in lista_espera[:cupos_liberados]:
                # Enviar notificación de cupo disponible
                pass
            
            messages.success(request, 'Capacidad actualizada correctamente')
        
        elif action == 'confirmar_taller':
            taller.estado = 'confirmado'
            taller.save()
            
            # Notificar a todos los inscritos
            from notifications.email_service import EmailService
            email_service = EmailService()
            for inscripcion in taller.inscripciones.filter(estado='confirmada'):
                email_service.enviar_confirmacion_taller(inscripcion)
            
            messages.success(request, 'Taller confirmado y participantes notificados')
        
        return redirect('gestionar_cupos', taller_id=taller_id)
    
    inscritos = taller.inscripciones.filter(estado='confirmada')
    lista_espera = ListaEspera.objects.filter(taller=taller, estado='activo')
    
    context = {
        'taller': taller,
        'inscritos': inscritos,
        'lista_espera': lista_espera,
        'cupos_disponibles': taller.capacidad_maxima - inscritos.count(),
    }
    
    return render(request, 'administracion/gestionar_cupos.html', context)

@staff_member_required
def gestionar_ponentes(request):
    """Vista para gestionar instructores/ponentes"""
    instructores = Usuario.objects.filter(rol='instructor').annotate(
        num_talleres=Count('talleres_impartidos'),
        evaluacion_promedio=Avg('talleres_impartidos__evaluaciones__satisfaccion_general')
    )
    
    if request.method == 'POST':
        # Crear o actualizar instructor
        pass
    
    context = {
        'instructores': instructores,
    }
    
    return render(request, 'administracion/gestionar_ponentes.html', context)
