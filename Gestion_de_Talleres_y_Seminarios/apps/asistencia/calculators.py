# apps/asistencia/calculators.py
from decimal import Decimal
from django.db.models import Count, Q


class AsistenciaCalculator:
    """Calculadora de porcentajes de asistencia"""
    
    @staticmethod
    def calcular_porcentaje(inscripcion):
        """
        Calcula el porcentaje de asistencia de una inscripción
        
        Args:
            inscripcion: Objeto Inscripcion
            
        Returns:
            Decimal: Porcentaje de asistencia (0-100)
        """
        total_sesiones = inscripcion.taller.sesiones.count()
        
        if total_sesiones == 0:
            return Decimal('0.00')
        
        # Contar asistencias (presente o tarde)
        asistencias = inscripcion.asistencias.filter(
            Q(estado='presente') | Q(estado='tarde')
        ).count()
        
        porcentaje = (Decimal(asistencias) / Decimal(total_sesiones)) * 100
        return round(porcentaje, 2)
    
    @staticmethod
    def califica_para_certificado(inscripcion, porcentaje_minimo=80):
        """
        Determina si un participante califica para certificado
        
        Args:
            inscripcion: Objeto Inscripcion
            porcentaje_minimo: Porcentaje mínimo requerido (default: 80)
            
        Returns:
            bool: True si califica, False si no
        """
        porcentaje = AsistenciaCalculator.calcular_porcentaje(inscripcion)
        return porcentaje >= porcentaje_minimo
    
    @staticmethod
    def actualizar_porcentaje_inscripcion(inscripcion):
        """
        Actualiza el campo porcentaje_asistencia en la inscripción
        
        Args:
            inscripcion: Objeto Inscripcion
        """
        porcentaje = AsistenciaCalculator.calcular_porcentaje(inscripcion)
        inscripcion.porcentaje_asistencia = porcentaje
        inscripcion.save(update_fields=['porcentaje_asistencia'])
        return porcentaje
    
    @staticmethod
    def obtener_estadisticas_taller(taller):
        """
        Obtiene estadísticas de asistencia de un taller
        
        Args:
            taller: Objeto Taller
            
        Returns:
            dict: Estadísticas de asistencia
        """
        inscripciones = taller.inscripciones.filter(estado='confirmada')
        total_inscritos = inscripciones.count()
        
        if total_inscritos == 0:
            return {
                'total_inscritos': 0,
                'promedio_asistencia': 0,
                'califican_certificado': 0,
                'no_califican_certificado': 0
            }
        
        # Calcular estadísticas
        califican = 0
        suma_porcentajes = Decimal('0.00')
        
        for inscripcion in inscripciones:
            porcentaje = AsistenciaCalculator.calcular_porcentaje(inscripcion)
            suma_porcentajes += porcentaje
            
            if porcentaje >= 80:
                califican += 1
        
        promedio = suma_porcentajes / total_inscritos
        
        return {
            'total_inscritos': total_inscritos,
            'promedio_asistencia': round(promedio, 2),
            'califican_certificado': califican,
            'no_califican_certificado': total_inscritos - califican,
            'porcentaje_califican': round((califican / total_inscritos) * 100, 2)
        }
    
    @staticmethod
    def obtener_estadisticas_sesion(sesion):
        """
        Obtiene estadísticas de una sesión específica
        
        Args:
            sesion: Objeto Sesion
            
        Returns:
            dict: Estadísticas de la sesión
        """
        asistencias = sesion.asistencia_set.all()
        total = asistencias.count()
        
        if total == 0:
            return {
                'total': 0,
                'presentes': 0,
                'ausentes': 0,
                'tardes': 0,
                'porcentaje_asistencia': 0
            }
        
        stats = asistencias.aggregate(
            presentes=Count('id', filter=Q(estado='presente')),
            ausentes=Count('id', filter=Q(estado='ausente')),
            tardes=Count('id', filter=Q(estado='tarde'))
        )
        
        asistieron = stats['presentes'] + stats['tardes']
        porcentaje = (asistieron / total) * 100
        
        return {
            'total': total,
            'presentes': stats['presentes'],
            'ausentes': stats['ausentes'],
            'tardes': stats['tardes'],
            'porcentaje_asistencia': round(porcentaje, 2)
        }