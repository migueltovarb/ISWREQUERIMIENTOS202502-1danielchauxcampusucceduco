# apps/pagos/wompi.py
try:
    import requests  # type: ignore
except Exception as e:
    raise ImportError(
        "The 'requests' library is required but could not be imported. "
        "Install it with: pip install requests"
    ) from e
from django.conf import settings

class WompiClient:
    BASE_URL = "https://production.wompi.co/v1" if settings.PRODUCTION else "https://sandbox.wompi.co/v1"
    
    def __init__(self):
        self.public_key = settings.WOMPI_PUBLIC_KEY
        self.private_key = settings.WOMPI_PRIVATE_KEY
    
    def crear_transaccion(self, monto, email, referencia):
        """Crea una transacción en Wompi"""
        url = f"{self.BASE_URL}/transactions"
        headers = {
            "Authorization": f"Bearer {self.private_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "amount_in_cents": int(monto * 100),  # Convertir a centavos
            "currency": "COP",
            "customer_email": email,
            "reference": referencia,
            "redirect_url": settings.WOMPI_REDIRECT_URL
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    
    def verificar_transaccion(self, transaction_id):
        """Verifica el estado de una transacción"""
        url = f"{self.BASE_URL}/transactions/{transaction_id}"
        headers = {"Authorization": f"Bearer {self.private_key}"}
        response = requests.get(url, headers=headers)
        return response.json()