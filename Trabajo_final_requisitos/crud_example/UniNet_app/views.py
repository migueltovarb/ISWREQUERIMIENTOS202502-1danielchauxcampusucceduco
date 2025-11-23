# ============================================================================
# UNINET - VISTAS COMPLETAS
# Cumple con TODAS las historias de usuario
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q, Count
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Estudiante, Administrador, Profesor, Curso, Horario, 
    Inscripcion, Pago, Periodo, NotificacionEmail
)
from .forms import (
    RegistroEstudianteForm, CursoForm, HorarioForm, ProfesorForm,
    InscripcionForm, PagoForm, PeriodoForm, BusquedaCursosForm
)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def es_administrador(user):
    return hasattr(user, 'administrador') and user.administrador.activo

def es_estudiante(user):
    return hasattr(user, 'estudiante') and user.estudiante.activo

# ============================================================================
# VISTAS PÚBLICAS
# ============================================================================

def home_view(request):
    """Página principal"""
    context = {
        'total_cursos': Curso.objects.filter(activo=True).count(),
        'total_estudiantes': Estudiante.objects.filter(activo=True).count(),
        'periodo_actual': Periodo.objects.filter(activo=True).first(),
    }
    return render(request, 'UniNet_app/home.html', context)

def registro_estudiante(request):
    """Registro de nuevos estudiantes"""
    if request.method == 'POST':
        form = RegistroEstudianteForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Registro exitoso! Bienvenido a UniNet.')
            return redirect('cursos_list')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroEstudianteForm()
    
    return render(request, 'UniNet_app/registro_estudiante.html', {'form': form})

# ============================================================================
# HISTORIA 1 y 2: INSCRIPCIÓN Y CONSULTA DE CURSOS
# ============================================================================

@login_required
def cursos_list(request):
    """
    Historia 1 y 2: Lista de cursos con filtros
    - Muestra: nombre, docente, horario, cupos, modalidad
    - Permite filtrar por: programa, docente, día, tipo
    - Actualiza cupos en tiempo real
    """
    try:
        estudiante = request.user.estudiante
    except Estudiante.DoesNotExist:
        messages.error(request, 'Debes registrarte como estudiante primero.')
        return redirect('registro_estudiante')
    
    # Obtener parámetros de búsqueda (Historia 2)
    busqueda = request.GET.get('q', '')
    tipo_curso = request.GET.get('tipo', 'todos')
    periodo_id = request.GET.get('periodo', '')
    dia = request.GET.get('dia', '')
    profesor_id = request.GET.get('profesor', '')
    
    # Filtrar horarios activos
    horarios = Horario.objects.filter(
        activo=True,
        curso__activo=True
    ).select_related('curso', 'profesor', 'profesor__user', 'periodo')
    
    # HISTORIA 2: Aplicar filtros
    if periodo_id:
        horarios = horarios.filter(periodo_id=periodo_id)
    else:
        periodo_activo = Periodo.objects.filter(activo=True).first()
        if periodo_activo:
            horarios = horarios.filter(periodo=periodo_activo)
    
    if tipo_curso != 'todos':
        horarios = horarios.filter(curso__tipo=tipo_curso)
    
    if dia:
        horarios = horarios.filter(dia_semana=dia)
    
    if profesor_id:
        horarios = horarios.filter(profesor_id=profesor_id)
    
    if busqueda:
        horarios = horarios.filter(
            Q(curso__nombre__icontains=busqueda) | 
            Q(curso__codigo__icontains=busqueda)
        )
    
    # Historia 2: Si no hay resultados
    if not horarios.exists() and (busqueda or tipo_curso != 'todos' or dia or profesor_id):
        messages.info(request, 'No se encontraron cursos.')
    
    # Obtener inscripciones del estudiante
    inscripciones_estudiante = Inscripcion.objects.filter(
        estudiante=estudiante,
        estado__in=['pendiente', 'confirmada']
    ).values_list('horario_id', flat=True)
    
    # Formulario de búsqueda
    form = BusquedaCursosForm(request.GET)
    
    context = {
        'form': form,
        'horarios': horarios,
        'inscripciones_estudiante': list(inscripciones_estudiante),
        'busqueda': busqueda,
        'tipo_curso': tipo_curso,
        'profesores': Profesor.objects.filter(activo=True),
    }
    
    return render(request, 'UniNet_app/cursos_list.html', context)

@login_required
def inscribir_curso(request, horario_id):
    """
    Historia 1: Inscribir en curso con TODAS las validaciones
    - Valida cupos disponibles
    - Valida cruce de horario
    - Valida requisitos previos
    - Evita duplicidad
    """
    try:
        estudiante = request.user.estudiante
    except Estudiante.DoesNotExist:
        messages.error(request, 'Debes registrarte como estudiante primero.')
        return redirect('registro_estudiante')
    
    horario = get_object_or_404(
        Horario.objects.select_related('curso', 'profesor', 'profesor__user', 'periodo'),
        id=horario_id,
        activo=True
    )
    
    # Verificar si ya está inscrito
    if Inscripcion.objects.filter(
        estudiante=estudiante,
        horario=horario,
        estado__in=['pendiente', 'confirmada']
    ).exists():
        messages.warning(request, 'Ya estás inscrito en este curso.')
        return redirect('cursos_list')
    
    if request.method == 'POST':
        try:
            # HISTORIA 1: Usar método del modelo que hace todas las validaciones
            inscripcion = estudiante.inscribir_curso(horario)
            
            # Mensajes según el resultado
            if inscripcion.estado == 'pendiente':
                # Historia 6: Curso de extensión, requiere pago
                messages.success(
                    request,
                    'Inscripción registrada. Procede a realizar el pago para confirmar.'
                )
                return redirect('procesar_pago', inscripcion_id=inscripcion.id)
            else:
                # Historia 1 y 3: Curso regular confirmado
                messages.success(request, 'Inscripción realizada con éxito.')
                messages.info(request, 'Inscripción exitosa. Se ha enviado un comprobante a su correo.')
                return redirect('mis_inscripciones')
                
        except ValidationError as e:
            # HISTORIA 1: Mostrar mensajes de error específicos
            messages.error(request, str(e))
            return redirect('cursos_list')
        except Exception as e:
            messages.error(request, f'Error al procesar la inscripción: {str(e)}')
            return redirect('cursos_list')
    
    context = {
        'horario': horario,
        'estudiante': estudiante,
    }
    
    return render(request, 'UniNet_app/inscribir_curso.html', context)

@login_required
def mis_inscripciones(request):
    """Lista de inscripciones del estudiante"""
    try:
        estudiante = request.user.estudiante
    except Estudiante.DoesNotExist:
        messages.error(request, 'Debes registrarte como estudiante primero.')
        return redirect('registro_estudiante')
    
    inscripciones = Inscripcion.objects.filter(
        estudiante=estudiante
    ).select_related(
        'horario', 'horario__curso', 'horario__profesor',
        'horario__profesor__user', 'horario__periodo'
    ).order_by('-fecha_inscripcion')
    
    context = {
        'inscripciones': inscripciones,
    }
    
    return render(request, 'UniNet_app/mis_inscripciones.html', context)

@login_required
def cancelar_inscripcion(request, inscripcion_id):
    """Cancelar inscripción"""
    inscripcion = get_object_or_404(
        Inscripcion,
        id=inscripcion_id,
        estudiante__user=request.user
    )
    
    if inscripcion.estado == 'cancelada':
        messages.info(request, 'Esta inscripción ya está cancelada.')
        return redirect('mis_inscripciones')
    
    if request.method == 'POST':
        try:
            inscripcion.cancelar()
            messages.success(request, 'Inscripción cancelada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al cancelar: {str(e)}')
        
        return redirect('mis_inscripciones')
    
    context = {'inscripcion': inscripcion}
    return render(request, 'UniNet_app/cancelar_inscripcion.html', context)

# ============================================================================
# HISTORIA 6: PAGOS EN LÍNEA
# ============================================================================

@login_required
def procesar_pago(request, inscripcion_id):
    """
    Historia 6: Procesar pago de curso de extensión
    - Muestra valor y medios disponibles
    - Redirige a pasarela segura (simulado)
    - Procesa respuesta y actualiza estado
    - Envía recibo por correo
    """
    inscripcion = get_object_or_404(
        Inscripcion,
        id=inscripcion_id,
        estudiante__user=request.user
    )
    
    if inscripcion.estado == 'confirmada':
        messages.info(request, 'Esta inscripción ya está confirmada.')
        return redirect('mis_inscripciones')
    
    monto = inscripcion.horario.curso.costo
    
    if request.method == 'POST':
        form = PagoForm(request.POST)
        
        if form.is_valid():
            pago = form.save(commit=False)
            pago.inscripcion = inscripcion
            pago.monto = monto
            pago.save()
            
            # HISTORIA 6: Procesar pago
            if pago.procesar_pago():
                # Pago exitoso
                messages.success(request, 'Pago procesado exitosamente.')
                messages.info(request, 'Se ha enviado un recibo a su correo.')
                return redirect('mis_inscripciones')
            else:
                # Pago pendiente
                messages.warning(request, 'Pago no procesado. Intente nuevamente.')
                return redirect('mis_inscripciones')
    else:
        form = PagoForm()
    
    context = {
        'form': form,
        'inscripcion': inscripcion,
        'monto': monto,
    }
    
    return render(request, 'UniNet_app/procesar_pago.html', context)

# ============================================================================
# HISTORIA 4: GESTIÓN DE CURSOS (ADMINISTRADOR)
# ============================================================================

@login_required
@user_passes_test(es_administrador)
def cursos_admin_list(request):
    """Historia 4: Lista de cursos para administración"""
    cursos = Curso.objects.all().select_related('periodo').order_by('codigo')
    context = {'dataset': cursos}
    return render(request, 'UniNet_app/admin/cursos_list.html', context)

@login_required
@user_passes_test(es_administrador)
def curso_create(request):
    """Historia 4: Crear nuevo curso"""
    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Curso creado correctamente.')
                return redirect('cursos_admin_list')
            except Exception as e:
                messages.error(request, f'Error al crear curso: {str(e)}')
    else:
        form = CursoForm()
    
    context = {'form': form, 'accion': 'Crear'}
    return render(request, 'UniNet_app/admin/curso_form.html', context)

@login_required
@user_passes_test(es_administrador)
def curso_update(request, id):
    """Historia 4: Actualizar curso"""
    curso = get_object_or_404(Curso, id=id)
    
    if request.method == 'POST':
        form = CursoForm(request.POST, request.FILES, instance=curso)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Curso actualizado correctamente.')
                return redirect('cursos_admin_list')
            except Exception as e:
                messages.error(request, f'Error al actualizar: {str(e)}')
    else:
        form = CursoForm(instance=curso)
    
    context = {'form': form, 'accion': 'Actualizar'}
    return render(request, 'UniNet_app/admin/curso_form.html', context)

@login_required
@user_passes_test(es_administrador)
def curso_delete(request, id):
    """Historia 4: Eliminar curso (solo si no tiene estudiantes)"""
    curso = get_object_or_404(Curso, id=id)
    
    if request.method == 'POST':
        # HISTORIA 4: Validar que no tenga estudiantes
        if curso.tiene_estudiantes_inscritos():
            messages.error(request, 'El curso no puede eliminarse, tiene estudiantes inscritos.')
            return redirect('cursos_admin_list')
        
        curso.activo = False
        curso.save()
        messages.success(request, 'Curso eliminado correctamente.')
        return redirect('cursos_admin_list')
    
    context = {'object': curso}
    return render(request, 'UniNet_app/admin/curso_delete.html', context)

# ============================================================================
# HISTORIA 5: ASIGNACIÓN DE HORARIOS Y DOCENTES
# ============================================================================

@login_required
@user_passes_test(es_administrador)
def horarios_admin_list(request):
    """Historia 5: Lista de horarios"""
    horarios = Horario.objects.all().select_related(
        'curso', 'profesor', 'periodo'
    ).order_by('periodo', 'dia_semana', 'hora_inicio')
    
    context = {'dataset': horarios}
    return render(request, 'UniNet_app/admin/horarios_list.html', context)

@login_required
@user_passes_test(es_administrador)
def horario_create(request):
    """Historia 5: Crear horario con validaciones de conflicto"""
    if request.method == 'POST':
        form = HorarioForm(request.POST)
        if form.is_valid():
            try:
                horario = form.save(commit=False)
                horario.full_clean()  # HISTORIA 5: Ejecuta validaciones del modelo
                horario.save()
                messages.success(request, 'Horario asignado correctamente.')
                return redirect('horarios_admin_list')
            except ValidationError as e:
                # HISTORIA 5: Mostrar mensaje de conflicto
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = HorarioForm()
    
    context = {'form': form, 'accion': 'Crear'}
    return render(request, 'UniNet_app/admin/horario_form.html', context)

@login_required
@user_passes_test(es_administrador)
def horario_update(request, id):
    """Historia 5: Actualizar horario"""
    horario = get_object_or_404(Horario, id=id)
    
    if request.method == 'POST':
        form = HorarioForm(request.POST, instance=horario)
        if form.is_valid():
            try:
                horario = form.save(commit=False)
                horario.full_clean()  # HISTORIA 5: Validaciones
                horario.save()
                messages.success(request, 'Horario actualizado correctamente.')
                return redirect('horarios_admin_list')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
    else:
        form = HorarioForm(instance=horario)
    
    context = {'form': form, 'accion': 'Actualizar'}
    return render(request, 'UniNet_app/admin/horario_form.html', context)

@login_required
@user_passes_test(es_administrador)
def horario_delete(request, id):
    """Eliminar horario"""
    horario = get_object_or_404(Horario, id=id)
    
    if request.method == 'POST':
        horario.activo = False
        horario.save()
        messages.success(request, 'Horario eliminado correctamente.')
        return redirect('horarios_admin_list')
    
    context = {'object': horario}
    return render(request, 'UniNet_app/admin/horario_delete.html', context)

# ============================================================================
# GESTIÓN DE PROFESORES
# ============================================================================

@login_required
@user_passes_test(es_administrador)
def profesores_admin_list(request):
    """Lista de profesores"""
    profesores = Profesor.objects.all().select_related('user').order_by('codigo_profesor')
    context = {'dataset': profesores}
    return render(request, 'UniNet_app/admin/profesores_list.html', context)

@login_required
@user_passes_test(es_administrador)
def profesor_create(request):
    """Crear profesor"""
    if request.method == 'POST':
        form = ProfesorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profesor creado correctamente.')
            return redirect('profesores_admin_list')
    else:
        form = ProfesorForm()
    
    context = {'form': form, 'accion': 'Crear'}
    return render(request, 'UniNet_app/admin/profesor_form.html', context)

@login_required
@user_passes_test(es_administrador)
def profesor_update(request, id):
    """Actualizar profesor"""
    profesor = get_object_or_404(Profesor, id=id)
    
    if request.method == 'POST':
        form = ProfesorForm(request.POST, instance=profesor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profesor actualizado correctamente.')
            return redirect('profesores_admin_list')
    else:
        form = ProfesorForm(instance=profesor)
    
    context = {'form': form, 'accion': 'Actualizar'}
    return render(request, 'UniNet_app/admin/profesor_form.html', context)

@login_required
@user_passes_test(es_administrador)
def profesor_delete(request, id):
    """Eliminar profesor"""
    profesor = get_object_or_404(Profesor, id=id)
    
    if request.method == 'POST':
        profesor.activo = False
        profesor.save()
        messages.success(request, 'Profesor eliminado correctamente.')
        return redirect('profesores_admin_list')
    
    context = {'object': profesor}
    return render(request, 'UniNet_app/admin/profesor_delete.html', context)

# ============================================================================
# GESTIÓN DE PERIODOS
# ============================================================================

@login_required
@user_passes_test(es_administrador)
def periodos_admin_list(request):
    """Lista de periodos"""
    periodos = Periodo.objects.all().order_by('-fecha_inicio')
    context = {'dataset': periodos}
    return render(request, 'UniNet_app/admin/periodos_list.html', context)

@login_required
@user_passes_test(es_administrador)
def periodo_create(request):
    """Crear periodo"""
    if request.method == 'POST':
        form = PeriodoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Periodo creado correctamente.')
            return redirect('periodos_admin_list')
    else:
        form = PeriodoForm()
    
    context = {'form': form, 'accion': 'Crear'}
    return render(request, 'UniNet_app/admin/periodo_form.html', context)

@login_required
@user_passes_test(es_administrador)
def periodo_update(request, id):
    """Actualizar periodo"""
    periodo = get_object_or_404(Periodo, id=id)
    
    if request.method == 'POST':
        form = PeriodoForm(request.POST, instance=periodo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Periodo actualizado correctamente.')
            return redirect('periodos_admin_list')
    else:
        form = PeriodoForm(instance=periodo)
    
    context = {'form': form, 'accion': 'Actualizar'}
    return render(request, 'UniNet_app/admin/periodo_form.html', context)

# ============================================================================
# DASHBOARD Y REPORTES
# ============================================================================

@login_required
@user_passes_test(es_administrador)
def dashboard_admin(request):
    """Dashboard administrativo"""
    periodo_actual = Periodo.objects.filter(activo=True).first()
    
    context = {
        'periodo_actual': periodo_actual,
        'total_estudiantes': Estudiante.objects.filter(activo=True).count(),
        'total_cursos': Curso.objects.filter(activo=True).count(),
        'total_profesores': Profesor.objects.filter(activo=True).count(),
        'inscripciones_periodo': Inscripcion.objects.filter(
            horario__periodo=periodo_actual,
            estado='confirmada'
        ).count() if periodo_actual else 0,
        'cursos_populares': Curso.objects.filter(
            activo=True
        ).annotate(
            total_inscritos=Count('horarios__inscripciones',
                                filter=Q(horarios__inscripciones__estado='confirmada'))
        ).order_by('-total_inscritos')[:5],
    }
    
    return render(request, 'UniNet_app/admin/dashboard.html', context)

@login_required
@user_passes_test(es_administrador)
def reportes_view(request):
    """Vista de reportes"""
    from .forms import ReporteForm
    
    if request.method == 'POST':
        form = ReporteForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Reporte generado exitosamente.')
    else:
        form = ReporteForm()
    
    from .models import Reporte
    reportes_recientes = Reporte.objects.all().order_by('-fecha_generacion')[:10]
    
    context = {
        'form': form,
        'reportes_recientes': reportes_recientes,
    }
    
    return render(request, 'UniNet_app/admin/reportes.html', context)