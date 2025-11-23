# apps/pagos/urls.py
from django.urls import path
from . import views

app_name = "pagos"

urlpatterns = [
    # Iniciar pago para una inscripción específica
    path('iniciar/<int:inscripcion_id>/', views.iniciar_pago, name='iniciar_pago'),

    # Resultado del pago
    path('resultado/', views.resultado_pago, name='resultado_pago'),

    # Ver comprobante de un pago
    path('comprobante/<int:pago_id>/', views.ver_comprobante, name='ver_comprobante'),

    # Webhook de Wompi
    path('webhook/', views.webhook_wompi, name='webhook_wompi'),
]

# apps/pagos/views.py (archivo adicional que falta)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Pago
from .wompi import WompiClient
import json
from django.urls import path
from . import views

urlpatterns = [
    path('iniciar/<int:inscripcion_id>/', views.iniciar_pago, name='iniciar_pago'),
    path('resultado/', views.resultado_pago, name='resultado_pago'),
    path('ver_comprobante/<int:pago_id>/', views.ver_comprobante, name='ver_comprobante'),
    path('webhook/', views.webhook_wompi, name='webhook_wompi'),
]


@login_required
def iniciar_pago(request, inscripcion_id):
    """
    Vista para iniciar proceso de pago con Wompi
    """
    inscripcion = get_object_or_404(inscripcion, id=inscripcion_id)
    
    # Verificar que sea el participante
    if inscripcion.participante != request.user:
        return HttpResponseForbidden("No puedes pagar esta inscripción")
    
    # Verificar que esté pendiente de pago
    if inscripcion.estado != 'pendiente_pago':
        messages.error(request, 'Esta inscripción ya fue procesada')
        return redirect('detalle_inscripcion', inscripcion_id=inscripcion.id)
    
    # Verificar que no haya expirado (30 minutos)
    from inscripciones.utils import InscripcionHelper
    tiempo = InscripcionHelper.calcular_tiempo_restante_pago(inscripcion)
    
    if tiempo['expiro']:
        inscripcion.estado = 'cancelada'
        inscripcion.save()
        messages.error(request, 'El tiempo para pagar ha expirado. Por favor inscríbete nuevamente.')
        return redirect('detalle_taller', taller_id=inscripcion.taller.id)
    
    try:
        # Crear o obtener pago existente
        pago, created = Pago.objects.get_or_create(
            inscripcion=inscripcion,
            defaults={
                'monto': inscripcion.taller.costo,
                'metodo': 'pendiente',
                'estado': 'pendiente'
            }
        )
        
        if created:
            # Crear transacción en Wompi
            wompi = WompiClient()
            resultado = wompi.crear_transaccion(
                monto=pago.monto,
                email=inscripcion.participante.email,
                referencia=f"TALLER-{inscripcion.id}-{pago.id}"
            )
            
            pago.referencia_wompi = resultado['data']['id']
            pago.save()
        
        # Obtener URL de pago
        wompi = WompiClient()
        info_transaccion = wompi.verificar_transaccion(pago.referencia_wompi)
        
        if 'payment_link_url' in info_transaccion['data']:
            return redirect(info_transaccion['data']['payment_link_url'])
        
        messages.error(request, 'Error al generar enlace de pago')
        return redirect('detalle_inscripcion', inscripcion_id=inscripcion.id)
        
    except Exception as e:
        messages.error(request, f'Error al procesar el pago: {e}')
        return redirect('detalle_inscripcion', inscripcion_id=inscripcion.id)


def resultado_pago(request):
    """
    Vista de resultado después del pago (redirect de Wompi)
    """
    transaction_id = request.GET.get('id')
    status = request.GET.get('status')
    
    if not transaction_id:
        messages.error(request, 'No se recibió información del pago')
        return redirect('mis_talleres')
    
    try:
        pago = Pago.objects.get(referencia_wompi=transaction_id)
        
        if status == 'APPROVED':
            messages.success(request, '¡Pago exitoso! Tu inscripción ha sido confirmada.')
        elif status == 'DECLINED':
            messages.error(request, 'El pago fue rechazado. Por favor intenta nuevamente.')
        elif status == 'PENDING':
            messages.info(request, 'Tu pago está en proceso de verificación.')
        else:
            messages.warning(request, 'Estado de pago desconocido.')
        
        return redirect('detalle_inscripcion', inscripcion_id=pago.inscripcion.id)
        
    except Pago.DoesNotExist:
        messages.error(request, 'No se encontró información del pago')
        return redirect('mis_talleres')


@csrf_exempt
def webhook_wompi(request):
    """
    Webhook para recibir notificaciones de Wompi sobre pagos
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Parsear datos del webhook
        data = json.loads(request.body)
        
        # Verificar firma (recomendado en producción)
        # signature = request.META.get('HTTP_X_SIGNATURE')
        # if not verificar_firma_wompi(data, signature):
        #     return HttpResponse(status=403)
        
        if data.get('event') == 'transaction.updated':
            transaction_data = data['data']['transaction']
            transaction_id = transaction_data['id']
            status = transaction_data['status']
            
            # Buscar el pago
            try:
                pago = Pago.objects.get(referencia_wompi=transaction_id)
            except Pago.DoesNotExist:
                print(f"Pago no encontrado para transacción: {transaction_id}")
                return HttpResponse(status=404)
            
            # Actualizar estado según respuesta de Wompi
            if status == 'APPROVED':
                pago.estado = 'aprobado'
                pago.fecha_pago = timezone.now()
                pago.metodo = transaction_data.get('payment_method_type', 'desconocido')
                pago.inscripcion.estado = 'confirmada'
                pago.inscripcion.save()
                
                # Enviar email de confirmación
                from notifications.email_service import EmailService
                try:
                    email_service = EmailService()
                    email_service.enviar_confirmacion_pago(pago)
                except Exception as e:
                    print(f"Error enviando email de confirmación: {e}")
                
            elif status == 'DECLINED':
                pago.estado = 'rechazado'
                
            elif status == 'ERROR':
                pago.estado = 'error'
            
            pago.save()
            
            print(f"Pago actualizado: {pago.id} - Estado: {pago.estado}")
        
        return HttpResponse(status=200)
        
    except json.JSONDecodeError:
        return HttpResponse(status=400)
    except Exception as e:
        print(f"Error en webhook: {e}")
        return HttpResponse(status=500)


@login_required
def ver_comprobante(request, pago_id):
    """
    Vista para ver el comprobante de pago
    """
    pago = get_object_or_404(Pago, id=pago_id)
    
    # Verificar permisos
    es_participante = pago.inscripcion.participante == request.user
    es_admin = request.user.rol == 'admin'
    
    if not (es_participante or es_admin):
        return HttpResponseForbidden("No tienes permiso para ver este comprobante")
    
    context = {
        'pago': pago,
    }
    
    return render(request, 'pagos/ver_comprobante.html', context)