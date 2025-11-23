# apps/materiales/views.py
from datetime import timezone
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from apps.inscripciones.models import Inscripcion
from apps.materiales.models import Material, DescargarMaterial


@login_required
def descargar_material(request, material_id):
    """Permite descargar material solo a inscritos"""
    material = get_object_or_404(Material, id=material_id)
    
    # Verificar que el usuario esté inscrito en el taller
    esta_inscrito = Inscripcion.objects.filter(
        taller=material.taller,
        participante=request.user,
        estado='confirmada'
    ).exists()
    
    if not esta_inscrito and not request.user.is_staff:
        raise Http404("No tienes acceso a este material")
    
    # Registrar descarga (analytics)
    DescargarMaterial.objects.create(
        material=material,
        usuario=request.user,
        fecha=timezone.now()
    )
    
    return FileResponse(
        material.archivo.open('rb'),
        as_attachment=True,
        filename=material.archivo.name
    )

def index(request):
    materiales = Material.objects.all()
    return render(request, 'materiales/index.html', {'materiales': materiales})