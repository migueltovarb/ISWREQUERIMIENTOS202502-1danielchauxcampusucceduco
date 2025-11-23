# apps/materiales/storage.py
import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils.text import slugify
from datetime import datetime


class MaterialStorage(FileSystemStorage):
    """
    Storage personalizado para materiales de talleres
    Organiza archivos por taller y fecha
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = os.path.join(settings.MEDIA_ROOT, 'materiales')
        self.base_url = f"{settings.MEDIA_URL}materiales/"
    
    def get_available_name(self, name, max_length=None):
        """
        Evita sobrescribir archivos con el mismo nombre
        """
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        
        # Si el archivo existe, agregar timestamp
        count = 1
        while self.exists(name):
            name = os.path.join(
                dir_name,
                f"{file_root}_{count}{file_ext}"
            )
            count += 1
        
        return name


def material_upload_path(instance, filename):
    """
    Genera ruta de subida para materiales
    Organiza por: materiales/taller_id/año/mes/filename
    
    Args:
        instance: Instancia del modelo Material
        filename: Nombre original del archivo
        
    Returns:
        str: Ruta donde se guardará el archivo
    """
    # Obtener extensión
    ext = filename.split('.')[-1]
    
    # Limpiar nombre del archivo
    filename_base = os.path.splitext(filename)[0]
    filename_clean = slugify(filename_base)
    
    # Generar nombre único con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_filename = f"{filename_clean}_{timestamp}.{ext}"
    
    # Estructura: materiales/taller_123/2025/01/archivo.pdf
    fecha = datetime.now()
    return os.path.join(
        'materiales',
        f'taller_{instance.taller.id}',
        str(fecha.year),
        str(fecha.month).zfill(2),
        new_filename
    )


class MaterialValidator:
    """Validador de archivos de materiales"""
    
    # Extensiones permitidas por tipo
    EXTENSIONES_PERMITIDAS = {
        'pdf': ['.pdf'],
        'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
        'presentacion': ['.ppt', '.pptx', '.odp', '.key'],
        'documento': ['.doc', '.docx', '.odt', '.txt', '.rtf'],
        'imagen': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
        'comprimido': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'otro': []
    }
    
    # Tamaños máximos por tipo (en MB)
    TAMANOS_MAXIMOS = {
        'pdf': 10,
        'video': 500,
        'presentacion': 50,
        'documento': 10,
        'imagen': 5,
        'comprimido': 100,
        'otro': 20
    }
    
    @staticmethod
    def validar_extension(archivo, tipo):
        """
        Valida que la extensión del archivo sea permitida
        
        Args:
            archivo: Archivo subido
            tipo: Tipo de material
            
        Returns:
            tuple: (bool, str) - (es_valido, mensaje)
        """
        if tipo == 'enlace':
            return True, "Enlace válido"
        
        nombre = archivo.name.lower()
        ext = os.path.splitext(nombre)[1]
        
        extensiones_permitidas = MaterialValidator.EXTENSIONES_PERMITIDAS.get(tipo, [])
        
        if tipo == 'otro':
            # Para "otro", permitir extensiones comunes
            todas_extensiones = []
            for exts in MaterialValidator.EXTENSIONES_PERMITIDAS.values():
                todas_extensiones.extend(exts)
            extensiones_permitidas = todas_extensiones
        
        if ext not in extensiones_permitidas:
            return False, f"Extensión {ext} no permitida para tipo {tipo}"
        
        return True, "Extensión válida"
    
    @staticmethod
    def validar_tamano(archivo, tipo):
        """
        Valida que el tamaño del archivo no exceda el límite
        
        Args:
            archivo: Archivo subido
            tipo: Tipo de material
            
        Returns:
            tuple: (bool, str) - (es_valido, mensaje)
        """
        if tipo == 'enlace':
            return True, "Enlace válido"
        
        tamano_mb = archivo.size / (1024 * 1024)
        tamano_maximo = MaterialValidator.TAMANOS_MAXIMOS.get(tipo, 20)
        
        if tamano_mb > tamano_maximo:
            return False, f"El archivo excede el tamaño máximo de {tamano_maximo}MB"
        
        return True, f"Tamaño válido ({tamano_mb:.2f}MB)"
    
    @staticmethod
    def validar_archivo_completo(archivo, tipo):
        """
        Realiza todas las validaciones sobre un archivo
        
        Args:
            archivo: Archivo subido
            tipo: Tipo de material
            
        Returns:
            dict: Resultado de validaciones
        """
        if tipo == 'enlace':
            return {
                'valido': True,
                'errores': [],
                'warnings': []
            }
        
        resultado = {
            'valido': True,
            'errores': [],
            'warnings': []
        }
        
        # Validar extensión
        valido_ext, msg_ext = MaterialValidator.validar_extension(archivo, tipo)
        if not valido_ext:
            resultado['valido'] = False
            resultado['errores'].append(msg_ext)
        
        # Validar tamaño
        valido_tam, msg_tam = MaterialValidator.validar_tamano(archivo, tipo)
        if not valido_tam:
            resultado['valido'] = False
            resultado['errores'].append(msg_tam)
        else:
            # Agregar warning si el archivo es muy grande (>50% del límite)
            tamano_mb = archivo.size / (1024 * 1024)
            tamano_maximo = MaterialValidator.TAMANOS_MAXIMOS.get(tipo, 20)
            
            if tamano_mb > (tamano_maximo * 0.5):
                resultado['warnings'].append(
                    f"El archivo es grande ({tamano_mb:.2f}MB). Considera comprimirlo."
                )
        
        return resultado


class MaterialHelper:
    """Funciones auxiliares para manejo de materiales"""
    
    @staticmethod
    def obtener_icono_tipo(tipo):
        """
        Retorna el icono FontAwesome apropiado para el tipo de material
        
        Args:
            tipo: Tipo de material
            
        Returns:
            str: Clase CSS de FontAwesome
        """
        iconos = {
            'pdf': 'fa-file-pdf',
            'video': 'fa-file-video',
            'presentacion': 'fa-file-powerpoint',
            'documento': 'fa-file-word',
            'imagen': 'fa-file-image',
            'enlace': 'fa-link',
            'comprimido': 'fa-file-archive',
            'otro': 'fa-file'
        }
        
        return iconos.get(tipo, 'fa-file')
    
    @staticmethod
    def formatear_tamano(bytes_size):
        """
        Formatea el tamaño en bytes a formato legible
        
        Args:
            bytes_size: Tamaño en bytes
            
        Returns:
            str: Tamaño formateado (ej: "2.5 MB")
        """
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def es_descargable(material):
        """
        Determina si un material es descargable (tiene archivo)
        
        Args:
            material: Instancia de Material
            
        Returns:
            bool: True si es descargable
        """
        return material.tipo != 'enlace' and bool(material.archivo)
    
    @staticmethod
    def limpiar_materiales_huerfanos():
        """
        Elimina archivos de materiales que ya no tienen registro en BD
        Debe ejecutarse como tarea programada
        
        Returns:
            dict: Estadísticas de limpieza
        """
        from .models import Material
        import os
        from django.conf import settings
        
        materiales_path = os.path.join(settings.MEDIA_ROOT, 'materiales')
        
        if not os.path.exists(materiales_path):
            return {
                'archivos_revisados': 0,
                'archivos_eliminados': 0,
                'espacio_liberado': 0
            }
        
        archivos_revisados = 0
        archivos_eliminados = 0
        espacio_liberado = 0
        
        # Obtener todos los paths de materiales en BD
        materiales_db = set()
        for material in Material.objects.all():
            if material.archivo:
                materiales_db.add(material.archivo.path)
        
        # Recorrer archivos en disco
        for root, dirs, files in os.walk(materiales_path):
            for file in files:
                file_path = os.path.join(root, file)
                archivos_revisados += 1
                
                # Si el archivo no está en BD, eliminarlo
                if file_path not in materiales_db:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        archivos_eliminados += 1
                        espacio_liberado += file_size
                    except Exception as e:
                        print(f"Error eliminando {file_path}: {e}")
        
        return {
            'archivos_revisados': archivos_revisados,
            'archivos_eliminados': archivos_eliminados,
            'espacio_liberado': espacio_liberado,
            'espacio_liberado_mb': espacio_liberado / (1024 * 1024)
        }
    
    @staticmethod
    def obtener_estadisticas_almacenamiento():
        """
        Obtiene estadísticas de uso de almacenamiento
        
        Returns:
            dict: Estadísticas de almacenamiento
        """
        from .models import Material
        from django.db.models import Sum, Count, Q
        import os
        from django.conf import settings
        
        # Estadísticas de BD
        stats = Material.objects.aggregate(
            total_materiales=Count('id'),
            total_con_archivo=Count('archivo', filter=~Q(archivo=''))
        )
        
        # Calcular espacio usado
        materiales_path = os.path.join(settings.MEDIA_ROOT, 'materiales')
        espacio_usado = 0
        
        if os.path.exists(materiales_path):
            for root, dirs, files in os.walk(materiales_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        espacio_usado += os.path.getsize(file_path)
                    except:
                        pass
        
        # Estadísticas por tipo
        stats_por_tipo = Material.objects.values('tipo').annotate(
            count=Count('id')
        )
        
        return {
            'total_materiales': stats['total_materiales'],
            'total_con_archivo': stats['total_con_archivo'],
            'espacio_usado_bytes': espacio_usado,
            'espacio_usado_mb': espacio_usado / (1024 * 1024),
            'espacio_usado_gb': espacio_usado / (1024 * 1024 * 1024),
            'por_tipo': list(stats_por_tipo)
        }