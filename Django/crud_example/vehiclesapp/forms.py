# vehiclesapp/forms.py (¡Crea este archivo!)

from django import forms
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    # La clase Meta le dice al formulario qué modelo usar y qué campos incluir.
    class Meta:
        model = Vehicle
        fields = ['name', 'brand', 'year'] # Usa todos los campos del modelo