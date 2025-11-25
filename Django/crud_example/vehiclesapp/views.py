from django.shortcuts import render, redirect, get_object_or_404
from .models import Vehicle 
from .forms import VehicleForm 

# =================================================================
# 1. READ (LISTAR) - Muestra todos los vehículos
# =================================================================
def vehicle_list(request):
    """
    Recupera todos los vehículos para mostrarlos.
    """
    vehicles = Vehicle.objects.all() 
    context = {'vehicles': vehicles}
    return render(request, 'vehiclesapp/vehicle_list.html', context)


# =================================================================
# 2. CREATE (CREAR) - Permite añadir un nuevo vehículo
# =================================================================
def vehicle_create(request):
    """
    Muestra o procesa el formulario para crear un nuevo vehículo.
    """
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('vehicle_list') 
    
    else:
        form = VehicleForm()
        
    context = {'form': form}
    return render(request, 'vehiclesapp/vehicle_form.html', context)


# =================================================================
# 3. UPDATE (ACTUALIZAR) - Permite editar un vehículo existente
# =================================================================
def vehicle_update(request, pk):
    """
    Busca un vehículo por ID (pk) y permite editar sus datos.
    """
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        # Al actualizar, pasamos request.POST (los nuevos datos) y instance=vehicle (el objeto original)
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save() # Guarda los cambios
            return redirect('vehicle_list')
    else:
        # En GET, cargamos el formulario con los datos existentes
        form = VehicleForm(instance=vehicle)
        
    context = {'form': form}
    return render(request, 'vehiclesapp/vehicle_form.html', context)


# =================================================================
# 4. DELETE (ELIMINAR) - Elimina un vehículo
# =================================================================
def vehicle_delete(request, pk):
    """
    Elimina un vehículo específico de la base de datos.
    """
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    # Ejecuta la acción de eliminación y redirige
    vehicle.delete() 
    return redirect('vehicle_list')