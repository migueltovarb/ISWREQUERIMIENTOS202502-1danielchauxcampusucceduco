# apps/pagos/views.py
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone  # <- corregido
from django.views.decorators.csrf import csrf_exempt

from apps.inscripciones.models import Inscripcion  # <- asegurarse que esta app exista y esté en INSTALLED_APPS
from .models import Pago
from .wompi import WompiClient


def iniciar_pago(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)

    # Crear registro de pago
    pago = Pago.objects.create(
        inscripcion=inscripcion,
        monto=inscripcion.taller.costo,
        metodo='pendiente',
        estado='pendiente'
    )

    # Crear transacción en Wompi
    wompi = WompiClient()
    resultado = wompi.crear_transaccion(
        monto=pago.monto,
        email=inscripcion.participante.email,
        referencia=f"TALLER-{inscripcion.id}"
    )

    pago.referencia_wompi = resultado['data']['id']
    pago.save()

    # Redirigir al link de Wompi
    return redirect(resultado['data']['payment_link_url'])


def enviar_email_confirmacion_pago(pago):
    """Función temporal para enviar correo de confirmación"""
    # Aquí puedes integrar django.core.mail o cualquier otra librería de email
    pass  # Implementar más adelante


@csrf_exempt
def webhook_wompi(request):
    """Webhook para recibir notificaciones de Wompi"""
    import json

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if data.get('event') == 'transaction.updated':
        transaction_id = data['data']['transaction']['id']
        estado = data['data']['transaction']['status']

        try:
            pago = Pago.objects.get(referencia_wompi=transaction_id)
        except Pago.DoesNotExist:
            return HttpResponse(status=404)

        if estado == 'APPROVED':
            pago.estado = 'aprobado'
            pago.fecha_pago = timezone.now()
            pago.inscripcion.estado = 'confirmada'
            pago.inscripcion.save()

            enviar_email_confirmacion_pago(pago)
        else:
            pago.estado = 'rechazado'

        pago.save()

    return HttpResponse(status=200)


def resultado_pago(request):
    return HttpResponse("Aquí se mostrará el resultado del pago.")


def ver_comprobante(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    if pago.comprobante:
        response = HttpResponse(pago.comprobante, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante_{pago.referencia_wompi}.pdf"'
        return response
    else:
        return HttpResponse("No hay comprobante disponible.", status=404)

