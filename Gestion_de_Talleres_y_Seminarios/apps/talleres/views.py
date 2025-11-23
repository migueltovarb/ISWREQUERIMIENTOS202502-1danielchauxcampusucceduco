# apps/talleres/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q, Count, Avg
from django.utils import timezone
from .models import Taller, Sesion
from apps.inscripciones.models import Inscripcion
from apps.core.models import Inscripcion
# from evaluaciones.analytics import EvaluacionAnalytics

def index(request):
    return render(request, 'talleres/index.html')


def catalogo_talleres(request):
    """
    Vista pública del catálogo de talleres
    """
    talleres = Taller.objects.filter(
        estado__in=['publicado', 'confirmado'],
        fecha_inicio__gte=timezone.now()
    ).annotate(
        num_inscritos=Count('inscripciones', filter=Q(inscripciones__estado='confirmada'))
    ).order_by('fecha_inicio')
    
    # Filtros
    modalidad = request.GET.get('modalidad')
    programa = request.GET.get('programa')
    busqueda = request.GET.get('busqueda')
    
    if modalidad:
        talleres = talleres.filter(modalidad=modalidad)
    
    if programa:
        talleres = talleres.filter(publico_objetivo__icontains=programa)
    
    if busqueda:
        talleres = talleres.filter(
            Q(titulo__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(instructor__first_name__icontains=busqueda) |
            Q(instructor__last_name__icontains=busqueda)
        )
    
    context = {
        'talleres': talleres,
        'modalidad_seleccionada': modalidad,
        'programa_seleccionado': programa,
        'busqueda': busqueda,
    }
    
    return render(request, 'talleres/catalogo.html', context)


def detalle_taller(request, taller_id):
    """
    Vista pública de detalle de un taller
    """
    taller = get_object_or_404(Taller, id=taller_id)
    
    # Verificar si el usuario está inscrito
    ya_inscrito = False
    inscripcion_usuario = None
    
    if request.user.is_authenticated:
        try:
            inscripcion_usuario = Inscripcion.objects.get(
                taller=taller,
                participante=request.user,
                estado__in=['confirmada', 'pendiente_pago']
            )
            ya_inscrito = True
        except Inscripcion.DoesNotExist:
            pass
    
    # Obtener sesiones
    sesiones = taller.sesiones.all().order_by('numero')
    
    # Obtener evaluaciones
    promedios = None  # EvaluacionAnalytics.obtener_promedio_taller(taller)
    
    # Calcular cupos
    inscritos = taller.inscripciones.filter(estado='confirmada').count()
    cupos_disponibles = taller.capacidad_maxima - inscritos
    porcentaje_ocupacion = (inscritos / taller.capacidad_maxima * 100) if taller.capacidad_maxima > 0 else 0
    
    context = {
        'taller': taller,
        'sesiones': sesiones,
        'ya_inscrito': ya_inscrito,
        'inscripcion': inscripcion_usuario,
        'promedios': promedios,
        'inscritos': inscritos,
        'cupos_disponibles': cupos_disponibles,
        'porcentaje_ocupacion': round(porcentaje_ocupacion, 1),
    }
    
    return render(request, 'talleres/detalle_taller.html', context)


@login_required
def crear_taller(request):
    """
    Vista para crear un nuevo taller
    Instructores crean talleres pendientes de aprobación
    Administradores crean talleres publicados directamente
    """
    if request.user.rol not in ['instructor', 'admin']:
        return HttpResponseForbidden("No tienes permiso para crear talleres")
    
    if request.method == 'POST':
        try:
            # Crear taller
            taller = Taller.objects.create(
                titulo=request.POST.get('titulo'),
                descripcion=request.POST.get('descripcion'),
                instructor_id=request.POST.get('instructor_id') if request.user.rol == 'admin' else request.user.id,
                modalidad=request.POST.get('modalidad'),
                fecha_inicio=request.POST.get('fecha_inicio'),
                fecha_fin=request.POST.get('fecha_fin'),
                duracion_horas=int(request.POST.get('duracion_horas')),
                capacidad_maxima=int(request.POST.get('capacidad_maxima')),
                capacidad_minima=int(request.POST.get('capacidad_minima')),
                costo=float(request.POST.get('costo', 0)),
                ubicacion=request.POST.get('ubicacion', ''),
                enlace_virtual=request.POST.get('enlace_virtual', ''),
                publico_objetivo=request.POST.get('publico_objetivo'),
                estado='publicado' if request.user.rol == 'admin' else 'pendiente_aprobacion'
            )
            
            # Si es virtual, generar enlace de Zoom
            if taller.modalidad in ['virtual', 'hibrida']:
                try:
                    taller.generar_enlace_zoom()
                except Exception as e:
                    messages.warning(request, f'Taller creado pero error al generar Zoom: {e}')
            
            if request.user.rol == 'admin':
                messages.success(request, 'Taller creado y publicado correctamente')
            else:
                messages.success(request, 'Taller creado. Está pendiente de aprobación administrativa')
            
            return redirect('detalle_taller', taller_id=taller.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear el taller: {e}')
    
    # GET: Mostrar formulario
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    instructores = User.objects.filter(rol='instructor') if request.user.rol == 'admin' else None
    
    context = {
        'instructores': instructores,
    }
    
    return render(request, 'talleres/crear_taller.html', context)


@login_required
def editar_taller(request, taller_id):
    """
    Vista para editar un taller existente
    """
    taller = get_object_or_404(Taller, id=taller_id)
    
    # Verificar permisos
    es_instructor = request.user == taller.instructor
    es_admin = request.user.rol == 'admin'
    
    if not (es_instructor or es_admin):
        return HttpResponseForbidden("No tienes permiso para editar este taller")
    
    if request.method == 'POST':
        try:
            # Verificar si hay cambios importantes que requieren notificar
            cambios_importantes = False
            
            if (request.POST.get('fecha_inicio') != str(taller.fecha_inicio) or
                request.POST.get('modalidad') != taller.modalidad):
                cambios_importantes = True
            
            # Actualizar taller
            taller.titulo = request.POST.get('titulo')
            taller.descripcion = request.POST.get('descripcion')
            taller.modalidad = request.POST.get('modalidad')
            taller.fecha_inicio = request.POST.get('fecha_inicio')
            taller.fecha_fin = request.POST.get('fecha_fin')
            taller.duracion_horas = int(request.POST.get('duracion_horas'))
            taller.capacidad_maxima = int(request.POST.get('capacidad_maxima'))
            taller.capacidad_minima = int(request.POST.get('capacidad_minima'))
            taller.costo = float(request.POST.get('costo', 0))
            taller.ubicacion = request.POST.get('ubicacion', '')
            taller.enlace_virtual = request.POST.get('enlace_virtual', '')
            taller.publico_objetivo = request.POST.get('publico_objetivo')
            taller.save()
            
            # Si hubo cambios importantes, notificar inscritos
            if cambios_importantes:
                from notifications.email_service import EmailService
                email_service = EmailService()
                
                inscripciones = taller.inscripciones.filter(estado='confirmada')
                for inscripcion in inscripciones:
                    email_service.enviar_notificacion_cambios(inscripcion, "Fecha y/o modalidad actualizada")
            
            messages.success(request, 'Taller actualizado correctamente')
            return redirect('detalle_taller', taller_id=taller.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el taller: {e}')
    
    context = {
        'taller': taller,
        'editando': True,
    }
    
    return render(request, 'talleres/crear_taller.html', context)


@login_required
def aprobar_taller(request, taller_id):
    """
    Vista para que administradores aprueben talleres
    """
    if request.user.rol != 'admin':
        return HttpResponseForbidden("Solo administradores pueden aprobar talleres")
    
    taller = get_object_or_404(Taller, id=taller_id)
    
    if request.method == 'POST':
        taller.estado = 'publicado'
        taller.save()
        
        # Notificar al instructor
        from notifications.email_service import EmailService
        email_service = EmailService()
        email_service.enviar_notificacion_aprobacion(taller)
        
        messages.success(request, f'Taller "{taller.titulo}" aprobado y publicado')
        return redirect('talleres_pendientes')
    
    context = {
        'taller': taller,
    }
    
    return render(request, 'talleres/confirmar_aprobacion.html', context)


@login_required
def rechazar_taller(request, taller_id):
    """
    Vista para que administradores rechacen talleres
    """
    if request.user.rol != 'admin':
        return HttpResponseForbidden("Solo administradores pueden rechazar talleres")
    
    taller = get_object_or_404(Taller, id=taller_id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        taller.estado = 'rechazado'
        taller.save()
        
        # Notificar al instructor
        from notifications.email_service import EmailService
        email_service = EmailService()
        email_service.enviar_notificacion_rechazo(taller, motivo)
        
        messages.success(request, 'Taller rechazado. El instructor ha sido notificado.')
        return redirect('talleres_pendientes')
    
    context = {
        'taller': taller,
    }
    
    return render(request, 'talleres/confirmar_rechazo.html', context)


@login_required
def talleres_pendientes(request):
    """
    Vista para que administradores vean talleres pendientes de aprobación
    """
    if request.user.rol != 'admin':
        return HttpResponseForbidden("Solo administradores pueden ver esta página")
    
    talleres = Taller.objects.filter(
        estado='pendiente_aprobacion'
    ).select_related('instructor').order_by('fecha_creacion')
    
    context = {
        'talleres': talleres,
    }
    
    return render(request, 'talleres/talleres_pendientes.html', context)


@login_required
def mis_talleres_instructor(request):
    """
    Vista para que instructores vean sus talleres
    """
    if request.user.rol != 'instructor':
        return HttpResponseForbidden("Esta vista es solo para instructores")
    
    talleres_proximos = Taller.objects.filter(
        instructor=request.user,
        fecha_inicio__gte=timezone.now(),
        estado__in=['publicado', 'confirmado']
    ).order_by('fecha_inicio')
    
    talleres_finalizados = Taller.objects.filter(
        instructor=request.user,
        estado='finalizado'
    ).order_by('-fecha_fin')[:10]
    
    talleres_pendientes = Taller.objects.filter(
        instructor=request.user,
        estado='pendiente_aprobacion'
    ).order_by('-fecha_creacion')
    
    # Estadísticas generales
    total_talleres = Taller.objects.filter(instructor=request.user).count()
    promedios = None  # EvaluacionAnalytics.obtener_promedio_instructor(request.user)
    
    context = {
        'talleres_proximos': talleres_proximos,
        'talleres_finalizados': talleres_finalizados,
        'talleres_pendientes': talleres_pendientes,
        'total_talleres': total_talleres,
        'promedios': promedios,
    }
    
    return render(request, 'talleres/mis_talleres_instructor.html', context)


@login_required
def cancelar_taller(request, taller_id):
    """
    Vista para cancelar un taller
    """
    taller = get_object_or_404(Taller, id=taller_id)
    
    # Verificar permisos
    es_instructor = request.user == taller.instructor
    es_admin = request.user.rol == 'admin'
    
    if not (es_instructor or es_admin):
        return HttpResponseForbidden("No tienes permiso para cancelar este taller")
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        taller.estado = 'cancelado'
        taller.save()
        
        # Notificar a todos los inscritos
        from notifications.email_service import EmailService
        email_service = EmailService()
        
        inscripciones = taller.inscripciones.filter(estado='confirmada')
        for inscripcion in inscripciones:
            email_service.enviar_notificacion_cancelacion_taller(inscripcion, motivo)
        
        messages.success(request, 'Taller cancelado. Todos los inscritos han sido notificados.')
        return redirect('mis_talleres_instructor' if es_instructor else 'dashboard_admin')
    
    context = {
        'taller': taller,
    }
    
    return render(request, 'talleres/confirmar_cancelacion.html', context)


@login_required
def clonar_taller(request, taller_id):
    """
    Vista para clonar un taller existente
    Útil para talleres que se repiten
    """
    taller_original = get_object_or_404(Taller, id=taller_id)
    
    # Verificar permisos
    es_instructor = request.user == taller_original.instructor
    es_admin = request.user.rol == 'admin'
    
    if not (es_instructor or es_admin):
        return HttpResponseForbidden("No tienes permiso para clonar este taller")
    
    if request.method == 'POST':
        # Clonar taller
        taller_nuevo = Taller.objects.create(
            titulo=f"{taller_original.titulo} (Copia)",
            descripcion=taller_original.descripcion,
            instructor=taller_original.instructor,
            modalidad=taller_original.modalidad,
            capacidad_maxima=taller_original.capacidad_maxima,
            capacidad_minima=taller_original.capacidad_minima,
            costo=taller_original.costo,
            ubicacion=taller_original.ubicacion,
            publico_objetivo=taller_original.publico_objetivo,
            duracion_horas=taller_original.duracion_horas,
            estado='borrador'
        )
        
        messages.success(request, 'Taller clonado. Ahora puedes editarlo y publicarlo.')
        return redirect('editar_taller', taller_id=taller_nuevo.id)
    
    context = {
        'taller': taller_original,
    }
    
    return render(request, 'talleres/confirmar_clonar.html', context)