# apps/videoconferencia/zoom_service.py
import jwt
import requests # type: ignore
from datetime import datetime, timedelta
from django.conf import settings

class ZoomService:
    BASE_URL = "https://api.zoom.us/v2"
    
    def __init__(self):
        self.api_key = settings.ZOOM_API_KEY
        self.api_secret = settings.ZOOM_API_SECRET
    
    def _generar_token(self):
        """Genera JWT token para autenticación"""
        payload = {
            'iss': self.api_key,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, self.api_secret, algorithm='HS256')
    
    def crear_reunion(self, taller):
        """Crea una reunión de Zoom para un taller"""
        url = f"{self.BASE_URL}/users/me/meetings"
        headers = {
            "Authorization": f"Bearer {self._generar_token()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "topic": taller.titulo,
            "type": 2,  # Reunión programada
            "start_time": taller.fecha_inicio.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration": taller.duracion_horas * 60,  # En minutos
            "timezone": "America/Bogota",
            "agenda": taller.descripcion[:200],
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "watermark": False,
                "use_pmi": False,
                "approval_type": 0,  # Aprobación automática
                "audio": "both",
                "auto_recording": "cloud",  # Grabación automática
                "waiting_room": True
            }
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            return {
                'id': data['id'],
                'join_url': data['join_url'],
                'start_url': data['start_url'],
                'password': data.get('password', '')
            }
        else:
            raise Exception(f"Error al crear reunión: {response.text}")
    
    def actualizar_reunion(self, meeting_id, taller):
        """Actualiza una reunión existente"""
        url = f"{self.BASE_URL}/meetings/{meeting_id}"
        headers = {
            "Authorization": f"Bearer {self._generar_token()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "topic": taller.titulo,
            "start_time": taller.fecha_inicio.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration": taller.duracion_horas * 60,
            "agenda": taller.descripcion[:200]
        }
        
        response = requests.patch(url, json=payload, headers=headers)
        return response.status_code == 204
    
    def eliminar_reunion(self, meeting_id):
        """Elimina una reunión"""
        url = f"{self.BASE_URL}/meetings/{meeting_id}"
        headers = {"Authorization": f"Bearer {self._generar_token()}"}
        
        response = requests.delete(url, headers=headers)
        return response.status_code == 204
    
    def obtener_grabaciones(self, meeting_id):
        """Obtiene las grabaciones de una reunión"""
        url = f"{self.BASE_URL}/meetings/{meeting_id}/recordings"
        headers = {"Authorization": f"Bearer {self._generar_token()}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None