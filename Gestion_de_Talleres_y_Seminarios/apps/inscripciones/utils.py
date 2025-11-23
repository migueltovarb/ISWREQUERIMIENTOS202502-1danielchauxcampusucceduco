# apps/inscripciones/utils.py
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


class InscripcionValidator:
    """Utilidades para validar inscripciones"""
    
    @staticmethod
    def validar_cupos_disponibles(taller):
        """
        Verifica si hay cupos disponibles en un taller
        
        Args:
            taller: Objeto Taller
            
        Returns:
            tuple: (bool, str) - (tiene_cupos, mensaje)
        """
        inscritos = taller.inscripciones.filter(
            estado__in=['confirmada', 'pendiente_pago']
        ).count()
        
        if inscritos >= taller.capacidad_maxima:
            return False, "No hay cupos disponibles"
        
        return True, f"Cupos disponibles: {taller.capacidad_maxima - inscritos}"
    
    @staticmethod
    def validar_conflicto_horario(usuario, taller):
        """
        Verifica si el usuario tiene conflictos de horario con otros talleres
        
        Args:
            usuario: Objeto Usuario
            taller: Objeto Taller
            
        Returns:
            tuple: (bool, list) - (tiene_conflicto, lista_talleres_conflicto)
        """
        from inscripciones.models import Inscripcion
        
        # Obtener inscripciones confirmadas del usuario
        inscripciones_activas = Inscripcion.objects.filter(
            participante=usuario,
            estado='confirmada'
        ).select_related('taller')
        
        talleres_conflicto = []
        
        for inscripcion in inscripciones_activas:
            taller_existente = inscripcion.taller
            
            # Verificar superposición de fechas
            if InscripcionValidator._hay_superposicion(
                taller.fecha_inicio,
                taller.fecha_fin,
                taller_existente.fecha_inicio,
                taller_existente.fecha_fin
            ):
                talleres_conflicto.append(taller_existente)
        
        tiene_conflicto = len(talleres_conflicto) > 0
        return tiene_conflicto, talleres_conflicto
    
    @staticmethod
    def _hay_superposicion(inicio1, fin1, inicio2, fin2):
        """
        Verifica si hay superposición entre dos rangos de fechas
        
        Args:
            inicio1, fin1: Rango 1
            inicio2, fin2: Rango 2
            
        Returns:
            bool: True si hay superposición
        """
        return inicio1 <= fin2 and inicio2 <= fin1
    
    @staticmethod
    def validar_usuario_verificado(usuario):
        """
        Verifica si el usuario tiene su email verificado
        
        Args:
            usuario: Objeto Usuario
            
        Returns:
            tuple: (bool, str) - (esta_verificado, mensaje)
        """
        if not usuario.email_verificado:
            return False, "Debes verificar tu correo electrónico antes de inscribirte"
        
        return True, "Usuario verificado"
    
    @staticmethod
    def validar_no_inscrito_previamente(usuario, taller):
        """
        Verifica si el usuario ya está inscrito en el taller
        
        Args:
            usuario: Objeto Usuario
            taller: Objeto Taller
            
        Returns:
            tuple: (bool, str) - (puede_inscribirse, mensaje)
        """
        from inscripciones.models import Inscripcion
        
        inscripcion_existente = Inscripcion.objects.filter(
            participante=usuario,
            taller=taller,
            estado__in=['confirmada', 'pendiente_pago']
        ).exists()
        
        if inscripcion_existente:
            return False, "Ya estás inscrito en este taller"
        
        return True, "Puede inscribirse"
    
    @staticmethod
    def validar_taller_disponible(taller):
        """
        Verifica si el taller está disponible para inscripciones
        
        Args:
            taller: Objeto Taller
            
        Returns:
            tuple: (bool, str) - (esta_disponible, mensaje)
        """
        if taller.estado not in ['publicado', 'confirmado']:
            return False, "Este taller no está disponible para inscripciones"
        
        if taller.fecha_inicio < timezone.now():
            return False, "Este taller ya comenzó"
        
        return True, "Taller disponible"
    
    @staticmethod
    def validar_inscripcion_completa(usuario, taller):
        """
        Realiza todas las validaciones necesarias para una inscripción
        
        Args:
            usuario: Objeto Usuario
            taller: Objeto Taller
            
        Returns:
            dict: Resultado de todas las validaciones
        """
        resultados = {
            'valido': True,
            'errores': [],
            'advertencias': []
        }
        
        # Validar usuario verificado
        verificado, msg = InscripcionValidator.validar_usuario_verificado(usuario)
        if not verificado:
            resultados['valido'] = False
            resultados['errores'].append(msg)
        
        # Validar taller disponible
        disponible, msg = InscripcionValidator.validar_taller_disponible(taller)
        if not disponible:
            resultados['valido'] = False
            resultados['errores'].append(msg)
        
        # Validar no inscrito previamente
        puede_inscribirse, msg = InscripcionValidator.validar_no_inscrito_previamente(usuario, taller)
        if not puede_inscribirse:
            resultados['valido'] = False
            resultados['errores'].append(msg)
        
        # Validar cupos disponibles
        hay_cupos, msg = InscripcionValidator.validar_cupos_disponibles(taller)
        if not hay_cupos:
            resultados['valido'] = False
            resultados['errores'].append(msg)
        
        # Verificar conflictos de horario (advertencia, no bloquea)
        tiene_conflicto, talleres = InscripcionValidator.validar_conflicto_horario(usuario, taller)
        if tiene_conflicto:
            nombres_talleres = ', '.join([t.titulo for t in talleres])
            resultados['advertencias'].append(
                f"Tienes conflicto de horario con: {nombres_talleres}"
            )
        
        return resultados


class InscripcionHelper:
    """Funciones auxiliares para manejo de inscripciones"""
    
    @staticmethod
    def puede_cancelar(inscripcion):
        """
        Verifica si una inscripción puede ser cancelada
        
        Args:
            inscripcion: Objeto Inscripcion
            
        Returns:
            tuple: (bool, str) - (puede_cancelar, mensaje)
        """
        if inscripcion.estado not in ['confirmada', 'pendiente_pago']:
            return False, "Esta inscripción ya no puede ser cancelada"
        
        # Verificar plazo de 24 horas
        limite_cancelacion = inscripcion.taller.fecha_inicio - timedelta(hours=24)
        
        if timezone.now() > limite_cancelacion:
            return False, "El plazo para cancelar ha vencido (24 horas antes del inicio)"
        
        return True, "Puede cancelar"
    
    @staticmethod
    def calcular_tiempo_restante_pago(inscripcion, minutos_limite=30):
        """
        Calcula el tiempo restante para completar un pago
        
        Args:
            inscripcion: Objeto Inscripcion
            minutos_limite: Minutos límite para pagar
            
        Returns:
            dict: Información del tiempo restante
        """
        if inscripcion.estado != 'pendiente_pago':
            return {
                'expiro': False,
                'minutos_restantes': 0,
                'mensaje': 'Inscripción ya confirmada'
            }
        
        tiempo_transcurrido = timezone.now() - inscripcion.fecha_inscripcion
        minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60
        minutos_restantes = minutos_limite - minutos_transcurridos
        
        if minutos_restantes <= 0:
            return {
                'expiro': True,
                'minutos_restantes': 0,
                'mensaje': 'El tiempo para completar el pago ha expirado'
            }
        
        return {
            'expiro': False,
            'minutos_restantes': int(minutos_restantes),
            'mensaje': f'Tienes {int(minutos_restantes)} minutos para completar el pago'
        }
    
    @staticmethod
    def limpiar_inscripciones_expiradas():
        """
        Cancela inscripciones pendientes de pago que han expirado
        Debe ejecutarse como tarea programada (Celery)
        
        Returns:
            int: Número de inscripciones canceladas
        """
        from inscripciones.models import Inscripcion
        
        limite = timezone.now() - timedelta(minutes=30)
        
        inscripciones_expiradas = Inscripcion.objects.filter(
            estado='pendiente_pago',
            fecha_inscripcion__lt=limite
        )
        
        count = inscripciones_expiradas.count()
        inscripciones_expiradas.update(estado='cancelada')
        
        return count
    
    @staticmethod
    def notificar_lista_espera(taller, cupos_liberados=1):
        """
        Notifica a personas en lista de espera sobre cupos disponibles
        
        Args:
            taller: Objeto Taller
            cupos_liberados: Número de cupos disponibles
            
        Returns:
            int: Número de personas notificadas
        """
        from inscripciones.models import ListaEspera
        
        personas_en_espera = ListaEspera.objects.filter(
            taller=taller,
            estado='activo'
        ).order_by('fecha_registro')[:cupos_liberados]
        
        notificados = 0
        
        for persona in personas_en_espera:
            try:
                # Aquí se enviaría el correo de notificación
                persona.estado = 'notificado'
                persona.save()
                notificados += 1
            except Exception as e:
                print(f"Error notificando a {persona.usuario.email}: {e}")
        
        return notificados
    
    @staticmethod
    def obtener_estadisticas_inscripcion(taller):
        """
        Obtiene estadísticas de inscripciones de un taller
        
        Args:
            taller: Objeto Taller
            
        Returns:
            dict: Estadísticas de inscripciones
        """
        from inscripciones.models import Inscripcion, ListaEspera
        
        total_inscripciones = taller.inscripciones.count()
        confirmadas = taller.inscripciones.filter(estado='confirmada').count()
        pendientes_pago = taller.inscripciones.filter(estado='pendiente_pago').count()
        canceladas = taller.inscripciones.filter(estado='cancelada').count()
        en_espera = ListaEspera.objects.filter(taller=taller, estado='activo').count()
        
        porcentaje_ocupacion = (confirmadas / taller.capacidad_maxima * 100) if taller.capacidad_maxima > 0 else 0
        alcanza_minimo = confirmadas >= taller.capacidad_minima
        
        return {
            'total_inscripciones': total_inscripciones,
            'confirmadas': confirmadas,
            'pendientes_pago': pendientes_pago,
            'canceladas': canceladas,
            'en_espera': en_espera,
            'cupos_disponibles': taller.capacidad_maxima - confirmadas,
            'porcentaje_ocupacion': round(porcentaje_ocupacion, 1),
            'alcanza_minimo': alcanza_minimo,
            'faltan_para_minimo': max(0, taller.capacidad_minima - confirmadas)
        }