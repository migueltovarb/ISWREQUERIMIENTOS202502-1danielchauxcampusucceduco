# apps/inscripciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from .models import Inscripcion, ListaEspera
from .utils import InscripcionValidator, InscripcionHelper
from apps.talleres.models import Taller
from apps.inscripciones.models import Inscripcion
from apps.core.models import Inscripcion

def index(request):
    return render(request, 'inscripciones/index.html')

@login_required
def inscribirse_taller(request, taller_id):
    """
    Vista para inscribirse en un taller
    """
    taller = get_object_or_404(Taller, id=taller_id)
    
    # Validar inscripción
    validacion = InscripcionValidator.validar_inscripcion_completa(request.user, taller)
    
    if not validacion['valido']:
        for error in validacion['errores']:
            messages.error(request, error)
        return redirect('detalle_taller', taller_id=taller.id)
    
    # Mostrar advertencias si las hay
    for advertencia in validacion['advertencias']:
        messages.warning(request, advertencia)
    
    if request.method == 'POST':
        confirmado = request.POST.get('confirmar') == 'si'
        
        if not confirmado:
            messages.info(request, 'Inscripción cancelada')
            return redirect('detalle_taller', taller_id=taller.id)
        
        # Crear inscripción
        try:
            inscripcion = Inscripcion.objects.create(
                taller=taller,
                participante=request.user,
                estado='pendiente_pago' if taller.costo > 0 else 'confirmada'
            )
            
            # Si el taller es gratuito, confirmar inmediatamente
            if taller.costo == 0:
                messages.success(
                    request,
                    f'¡Inscripción exitosa! Te hemos enviado un correo de confirmación.'
                )
                
                
                return redirect('mis_talleres')
            else:
                # Redirigir a pago
                messages.info(
                    request,
                    'Por favor completa el pago para confirmar tu inscripción'
                )
                return redirect('procesar_pago', inscripcion_id=inscripcion.id)
                
        except Exception as e:
            messages.error(request, f'Error al procesar la inscripción: {e}')
            return redirect('detalle_taller', taller_id=taller.id)
    
    # GET: Mostrar confirmación
    context = {
        'taller': taller,
        'validacion': validacion,
    }
    
    return render(request, 'inscripciones/confirmar_inscripcion.html', context)


@login_required
def cancelar_inscripcion(request, inscripcion_id):
    """
    Vista para cancelar una inscripción
    """
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    
    # Verificar que sea el participante
    if inscripcion.participante != request.user:
        return HttpResponseForbidden("No puedes cancelar esta inscripción")
    
    # Validar que se puede cancelar
    puede_cancelar, mensaje = InscripcionHelper.puede_cancelar(inscripcion)
    
    if not puede_cancelar:
        messages.error(request, mensaje)
        return redirect('mis_talleres')
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        # Cancelar inscripción
        inscripcion.estado = 'cancelada'
        inscripcion.save()
        
        # Liberar cupo y notificar lista de espera
        InscripcionHelper.notificar_lista_espera(inscripcion.taller, cupos_liberados=1)
        
        messages.success(request, 'Tu inscripción ha sido cancelada correctamente')
        return redirect('mis_talleres')
    
    context = {
        'inscripcion': inscripcion,
    }
    
    return render(request, 'inscripciones/cancelar_inscripcion.html', context)


@login_required
def mis_talleres(request):
    """
    Vista para que un participante vea sus talleres inscritos
    """
    inscripciones_activas = Inscripcion.objects.filter(
        participante=request.user,
        estado__in=['confirmada', 'pendiente_pago']
    ).select_related('taller').order_by('taller__fecha_inicio')
    
    inscripciones_completadas = Inscripcion.objects.filter(
        participante=request.user,
        estado='completada'
    ).select_related('taller').order_by('-taller__fecha_fin')
    
    inscripciones_canceladas = Inscripcion.objects.filter(
        participante=request.user,
        estado='cancelada'
    ).select_related('taller').order_by('-fecha_inscripcion')[:5]  # Últimas 5
    
    # Agregar información de tiempo para pagos pendientes
    for inscripcion in inscripciones_activas:
        if inscripcion.estado == 'pendiente_pago':
            inscripcion.tiempo_restante = InscripcionHelper.calcular_tiempo_restante_pago(inscripcion)
    
    context = {
        'inscripciones_activas': inscripciones_activas,
        'inscripciones_completadas': inscripciones_completadas,
        'inscripciones_canceladas': inscripciones_canceladas,
    }
    
    return render(request, 'inscripciones/mis_talleres.html', context)


@login_required
def unirse_lista_espera(request, taller_id):
    """
    Vista para unirse a la lista de espera de un taller
    """
    taller = get_object_or_404(Taller, id=taller_id)
    
    # Verificar que no haya cupos disponibles
    hay_cupos, _ = InscripcionValidator.validar_cupos_disponibles(taller)
    
    if hay_cupos:
        messages.error(request, 'Este taller aún tiene cupos disponibles. Puedes inscribirte directamente.')
        return redirect('detalle_taller', taller_id=taller.id)
    
    # Verificar que no esté ya en lista de espera
    ya_en_espera = ListaEspera.objects.filter(
        taller=taller,
        usuario=request.user,
        estado='activo'
    ).exists()
    
    if ya_en_espera:
        messages.info(request, 'Ya estás en la lista de espera de este taller')
        return redirect('detalle_taller', taller_id=taller.id)
    
    # Verificar que no esté inscrito
    ya_inscrito = Inscripcion.objects.filter(
        taller=taller,
        participante=request.user,
        estado__in=['confirmada', 'pendiente_pago']
    ).exists()
    
    if ya_inscrito:
        messages.error(request, 'Ya estás inscrito en este taller')
        return redirect('mis_talleres')
    
    if request.method == 'POST':
        # Agregar a lista de espera
        ListaEspera.objects.create(
            taller=taller,
            usuario=request.user
        )
        
        messages.success(
            request,
            'Te hemos agregado a la lista de espera. Te notificaremos si se libera un cupo.'
        )
        return redirect('detalle_taller', taller_id=taller.id)
    
    # Obtener posición en la lista
    posicion = ListaEspera.objects.filter(
        taller=taller,
        estado='activo'
    ).count() + 1
    
    context = {
        'taller': taller,
        'posicion_estimada': posicion,
    }
    
    return render(request, 'inscripciones/confirmar_lista_espera.html', context)


@login_required
def salir_lista_espera(request, espera_id):
    """
    Vista para salir de la lista de espera
    """
    espera = get_object_or_404(ListaEspera, id=espera_id)
    
    # Verificar que sea el usuario
    if espera.usuario != request.user:
        return HttpResponseForbidden("No puedes modificar esta lista de espera")
    
    if request.method == 'POST':
        espera.estado = 'cancelado'
        espera.save()
        
        messages.success(request, 'Has salido de la lista de espera')
        return redirect('detalle_taller', taller_id=espera.taller.id)
    
    context = {
        'espera': espera,
    }
    
    return render(request, 'inscripciones/confirmar_salir_espera.html', context)


@login_required
def detalle_inscripcion(request, inscripcion_id):
    """
    Vista para ver detalles de una inscripción
    """
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    
    # Verificar permisos
    es_participante = inscripcion.participante == request.user
    es_instructor = inscripcion.taller.instructor == request.user
    es_admin = request.user.rol == 'admin'
    
    if not (es_participante or es_instructor or es_admin):
        return HttpResponseForbidden("No tienes permiso para ver esta información")
    
    # Calcular información adicional
    puede_cancelar, mensaje_cancelacion = InscripcionHelper.puede_cancelar(inscripcion)
    
    if inscripcion.estado == 'pendiente_pago':
        tiempo_restante = InscripcionHelper.calcular_tiempo_restante_pago(inscripcion)
    else:
        tiempo_restante = None
    
    context = {
        'inscripcion': inscripcion,
        'puede_cancelar': puede_cancelar,
        'mensaje_cancelacion': mensaje_cancelacion,
        'tiempo_restante': tiempo_restante,
    }
    
    return render(request, 'inscripciones/detalle_inscripcion.html', context)


@login_required
def reporte_inscritos(request, taller_id):
    """
    Vista para generar reporte de inscritos de un taller
    Solo para instructores y administradores
    """
    taller = get_object_or_404(Taller, id=taller_id)
    
    # Verificar permisos
    es_instructor = request.user == taller.instructor
    es_admin = request.user.rol == 'admin'
    
    if not (es_instructor or es_admin):
        return HttpResponseForbidden("No tienes permiso para ver esta información")
    
    # Obtener inscripciones
    inscripciones = taller.inscripciones.filter(
        estado='confirmada'
    ).select_related('participante').order_by('participante__first_name')
    
    # Obtener estadísticas
    estadisticas = InscripcionHelper.obtener_estadisticas_inscripcion(taller)
    
    # Exportar a Excel si se solicita
    if request.GET.get('formato') == 'excel':
        return exportar_inscritos_excel(taller, inscripciones)
    
    # Exportar a PDF si se solicita
    if request.GET.get('formato') == 'pdf':
        return exportar_inscritos_pdf(taller, inscripciones)
    
    context = {
        'taller': taller,
        'inscripciones': inscripciones,
        'estadisticas': estadisticas,
    }
    
    return render(request, 'inscripciones/reporte_inscritos.html', context)


def exportar_inscritos_excel(taller, inscripciones):
    """Exporta lista de inscritos a Excel"""
    import openpyxl
    from openpyxl.styles import Font, Alignment
    from django.http import HttpResponse
    
    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inscritos"
    
    # Encabezados
    headers = ['#', 'Nombre Completo', 'Documento', 'Email', 'Celular', 
               'Programa Académico', 'Tipo', 'Fecha Inscripción']
    ws.append(headers)
    
    # Estilo de encabezados
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # Datos
    for idx, inscripcion in enumerate(inscripciones, start=1):
        ws.append([
            idx,
            inscripcion.participante.get_full_name(),
            inscripcion.participante.documento,
            inscripcion.participante.email,
            inscripcion.participante.celular,
            inscripcion.participante.programa_academico,
            inscripcion.participante.get_rol_display(),
            inscripcion.fecha_inscripcion.strftime('%Y-%m-%d %H:%M')
        ])
    
    # Ajustar anchos de columna
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Preparar respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=inscritos_{taller.id}.xlsx'
    
    wb.save(response)
    return response


def exportar_inscritos_pdf(taller, inscripciones):
    """Exporta lista de inscritos a PDF"""
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from django.http import HttpResponse
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    titulo = Paragraph(f"<b>Lista de Inscritos - {taller.titulo}</b>", styles['Title'])
    elements.append(titulo)
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de datos
    data = [['#', 'Nombre', 'Documento', 'Email', 'Celular', 'Programa']]
    
    for idx, inscripcion in enumerate(inscripciones, start=1):
        data.append([
            str(idx),
            inscripcion.participante.get_full_name(),
            inscripcion.participante.documento,
            inscripcion.participante.email,
            inscripcion.participante.celular,
            inscripcion.participante.programa_academico
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=inscritos_{taller.id}.pdf'
    
    return response


@login_required
def api_verificar_disponibilidad(request, taller_id):
    """
    API endpoint para verificar disponibilidad de un taller (AJAX)
    """
    taller = get_object_or_404(Taller, id=taller_id)
    
    validacion = InscripcionValidator.validar_inscripcion_completa(request.user, taller)
    
    return JsonResponse({
        'valido': validacion['valido'],
        'errores': validacion['errores'],
        'advertencias': validacion['advertencias'],
        'cupos_disponibles': taller.cupos_disponibles
    })