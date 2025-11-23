# apps/evaluaciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Evaluacion
from .analytics import AnalyticsEvaluacion
from apps.inscripciones.models import Inscripcion
from apps.talleres.models import Taller


@login_required
def evaluar_taller(request, inscripcion_id):
    """
    Vista para que un participante evalúe un taller
    """
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    
    # Verificar que sea el participante
    if inscripcion.participante != request.user:
        return HttpResponseForbidden("No tienes permiso para evaluar este taller")
    
    # Verificar que el taller haya finalizado
    if inscripcion.taller.estado != 'finalizado':
        messages.error(request, 'No puedes evaluar un taller que aún no ha finalizado')
        return redirect('mis_talleres')
    
    # Verificar si ya evaluó
    if hasattr(inscripcion, 'evaluacion'):
        messages.info(request, 'Ya has evaluado este taller')
        return redirect('ver_evaluacion', inscripcion_id=inscripcion.id)
    
    if request.method == 'POST':
        try:
            # Crear evaluación
            evaluacion = Evaluacion.objects.create(
                inscripcion=inscripcion,
                calificacion_contenido=int(request.POST.get('calificacion_contenido')),
                calificacion_metodologia=int(request.POST.get('calificacion_metodologia')),
                calificacion_dominio_ponente=int(request.POST.get('calificacion_dominio_ponente')),
                calificacion_pertinencia=int(request.POST.get('calificacion_pertinencia')),
                satisfaccion_general=int(request.POST.get('satisfaccion_general')),
                comentarios=request.POST.get('comentarios', ''),
                aspectos_mejorar=request.POST.get('aspectos_mejorar', ''),
                fortalezas=request.POST.get('fortalezas', ''),
                recomendaria=request.POST.get('recomendaria') == 'true'
            )
            
            # Actualizar promedio del taller
            promedios = AnalyticsEvaluacion.obtener_promedio_taller(inscripcion.taller)
            inscripcion.taller.calificacion_promedio = promedios['promedio_total']
            inscripcion.taller.save(update_fields=['calificacion_promedio'])
            
            messages.success(request, '¡Gracias por tu evaluación! Ahora puedes descargar tu certificado.')
            return redirect('descargar_certificado', inscripcion_id=inscripcion.id)
            
        except Exception as e:
            messages.error(request, f'Error al guardar la evaluación: {e}')
    
    context = {
        'inscripcion': inscripcion,
        'taller': inscripcion.taller,
    }
    
    return render(request, 'evaluaciones/evaluar_taller.html', context)


@login_required
def ver_evaluacion(request, inscripcion_id):
    """
    Vista para que un participante vea su evaluación
    """
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    
    # Verificar permisos
    if inscripcion.participante != request.user and request.user.rol != 'admin':
        return HttpResponseForbidden("No tienes permiso para ver esta evaluación")
    
    try:
        evaluacion = inscripcion.evaluacion
    except Evaluacion.DoesNotExist:
        messages.error(request, 'No has evaluado este taller aún')
        return redirect('evaluar_taller', inscripcion_id=inscripcion.id)
    
    context = {
        'inscripcion': inscripcion,
        'evaluacion': evaluacion,
        'calificaciones': evaluacion.get_calificaciones_dict(),
    }
    
    return render(request, 'evaluaciones/ver_evaluacion.html', context)


@login_required
def evaluaciones_taller(request, taller_id):
    """
    Vista para que instructores vean las evaluaciones de su taller
    Las evaluaciones son anónimas
    """
    taller = get_object_or_404(Taller, id=taller_id)
    
    # Verificar permisos
    es_instructor = request.user == taller.instructor
    es_admin = request.user.rol == 'admin'
    
    if not (es_instructor or es_admin):
        return HttpResponseForbidden("No tienes permiso para ver estas evaluaciones")
    
    # Obtener evaluaciones (sin mostrar nombres)
    evaluaciones = Evaluacion.objects.filter(
        inscripcion__taller=taller
    ).order_by('-fecha_evaluacion')
    
    # Obtener estadísticas
    promedios = AnalyticsEvaluacion.obtener_promedio_taller(taller)
    distribucion = AnalyticsEvaluacion.obtener_distribucion_calificaciones(taller)
    comentarios_destacados = AnalyticsEvaluacion.obtener_comentarios_destacados(taller)
    areas_mejora = AnalyticsEvaluacion.obtener_areas_mejora(taller)
    tasa_recomendacion = AnalyticsEvaluacion.obtener_tasa_recomendacion(taller)
    
    context = {
        'taller': taller,
        'evaluaciones': evaluaciones,
        'promedios': promedios,
        'distribucion': distribucion,
        'comentarios_destacados': comentarios_destacados,
        'areas_mejora': areas_mejora,
        'tasa_recomendacion': tasa_recomendacion,
    }
    
    return render(request, 'evaluaciones/evaluaciones_taller.html', context)


@login_required
def mis_evaluaciones(request):
    """
    Vista para que un participante vea todas sus evaluaciones
    """
    evaluaciones = Evaluacion.objects.filter(
        inscripcion__participante=request.user
    ).select_related('inscripcion__taller').order_by('-fecha_evaluacion')
    
    context = {
        'evaluaciones': evaluaciones,
    }
    
    return render(request, 'evaluaciones/mis_evaluaciones.html', context)


@login_required
def estadisticas_instructor(request, instructor_id=None):
    """
    Vista para ver estadísticas de evaluaciones de un instructor
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if instructor_id:
        # Ver estadísticas de otro instructor (solo admins)
        if request.user.rol != 'admin':
            return HttpResponseForbidden("Solo administradores pueden ver esta información")
        instructor = get_object_or_404(User, id=instructor_id, rol='instructor')
    else:
        # Ver propias estadísticas
        if request.user.rol != 'instructor':
            return HttpResponseForbidden("Esta vista es solo para instructores")
        instructor = request.user
    
    # Obtener estadísticas generales
    promedios = AnalyticsEvaluacion.obtener_promedio_instructor(instructor)
    comparacion_talleres = AnalyticsEvaluacion.comparar_talleres_instructor(instructor)
    tendencia = AnalyticsEvaluacion.obtener_tendencia_instructor(instructor)
    
    # Obtener talleres del instructor
    talleres = Taller.objects.filter(
        instructor=instructor,
        estado='finalizado'
    ).order_by('-fecha_fin')
    
    context = {
        'instructor': instructor,
        'promedios': promedios,
        'comparacion_talleres': comparacion_talleres,
        'tendencia': tendencia,
        'talleres': talleres,
    }
    
    return render(request, 'evaluaciones/estadisticas_instructor.html', context)


@login_required
def reporte_evaluaciones_general(request):
    """
    Vista para administradores: reporte general de evaluaciones
    """
    if request.user.rol != 'admin':
        return HttpResponseForbidden("Solo administradores pueden ver esta información")
    
    from django.contrib.auth import get_user_model
    from django.db.models import Avg, Count
    
    User = get_user_model()
    
    # Top 10 talleres mejor evaluados
    top_talleres = Taller.objects.filter(
        estado='finalizado'
    ).annotate(
        num_evaluaciones=Count('inscripciones__evaluacion'),
        promedio=Avg('inscripciones__evaluacion__satisfaccion_general')
    ).filter(
        num_evaluaciones__gte=3  # Mínimo 3 evaluaciones
    ).order_by('-promedio')[:10]
    
    # Top 10 instructores mejor evaluados
    top_instructores = User.objects.filter(
        rol='instructor'
    ).annotate(
        num_evaluaciones=Count('talleres_impartidos__inscripciones__evaluacion'),
        promedio=Avg('talleres_impartidos__inscripciones__evaluacion__satisfaccion_general')
    ).filter(
        num_evaluaciones__gte=5  # Mínimo 5 evaluaciones
    ).order_by('-promedio')[:10]
    
    # Estadísticas generales
    total_evaluaciones = Evaluacion.objects.count()
    promedio_global = Evaluacion.objects.aggregate(
        Avg('satisfaccion_general')
    )['satisfaccion_general__avg'] or 0
    
    tasa_recomendacion_global = Evaluacion.objects.filter(
        recomendaria=True
    ).count() / total_evaluaciones * 100 if total_evaluaciones > 0 else 0
    
    context = {
        'top_talleres': top_talleres,
        'top_instructores': top_instructores,
        'total_evaluaciones': total_evaluaciones,
        'promedio_global': round(promedio_global, 2),
        'tasa_recomendacion_global': round(tasa_recomendacion_global, 1),
    }
    
    return render(request, 'evaluaciones/reporte_general.html', context)


@login_required
def editar_evaluacion(request, inscripcion_id):
    """
    Vista para editar una evaluación existente
    """
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    
    # Verificar que sea el participante
    if inscripcion.participante != request.user:
        return HttpResponseForbidden("No tienes permiso para editar esta evaluación")
    
    try:
        evaluacion = inscripcion.evaluacion
    except Evaluacion.DoesNotExist:
        messages.error(request, 'No has evaluado este taller aún')
        return redirect('evaluar_taller', inscripcion_id=inscripcion.id)
    
    if request.method == 'POST':
        try:
            # Actualizar evaluación
            evaluacion.calificacion_contenido = int(request.POST.get('calificacion_contenido'))
            evaluacion.calificacion_metodologia = int(request.POST.get('calificacion_metodologia'))
            evaluacion.calificacion_dominio_ponente = int(request.POST.get('calificacion_dominio_ponente'))
            evaluacion.calificacion_pertinencia = int(request.POST.get('calificacion_pertinencia'))
            evaluacion.satisfaccion_general = int(request.POST.get('satisfaccion_general'))
            evaluacion.comentarios = request.POST.get('comentarios', '')
            evaluacion.aspectos_mejorar = request.POST.get('aspectos_mejorar', '')
            evaluacion.fortalezas = request.POST.get('fortalezas', '')
            evaluacion.recomendaria = request.POST.get('recomendaria') == 'true'
            evaluacion.save()
            
            # Actualizar promedio del taller
            promedios = AnalyticsEvaluacion.obtener_promedio_taller(inscripcion.taller)
            inscripcion.taller.calificacion_promedio = promedios['promedio_total']
            inscripcion.taller.save(update_fields=['calificacion_promedio'])
            
            messages.success(request, 'Evaluación actualizada correctamente')
            return redirect('ver_evaluacion', inscripcion_id=inscripcion.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar la evaluación: {e}')
    
    context = {
        'inscripcion': inscripcion,
        'evaluacion': evaluacion,
        'editando': True,
    }
    
    return render(request, 'evaluaciones/evaluar_taller.html', context)