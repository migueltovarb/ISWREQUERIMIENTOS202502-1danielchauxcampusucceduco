# ============================================================================
# FORMULARIO: Búsqueda de Cursos - HISTORIA 2
# ============================================================================

from django import forms
from .models import Periodo, Profesor, Horario

class BusquedaCursosForm(forms.Form):
    """
    Historia 2: Formulario para buscar y filtrar cursos.
    Permite filtrar por: Programa, Docente, Día, Tipo de curso
    """
    q = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o código...'
        })
    )
    
    tipo = forms.ChoiceField(
        required=False,
        label='Tipo de Curso',
        choices=[
            ('todos', 'Todos'),
            ('regular', 'Ordinario'),
            ('extension', 'Extensión')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    periodo = forms.ModelChoiceField(
        queryset=Periodo.objects.filter(activo=True),
        required=False,
        label='Periodo',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Todos los periodos'
    )
    
    # HISTORIA 2: Filtro por día
    dia = forms.ChoiceField(
        required=False,
        label='Día',
        choices=[
            ('', 'Todos los días'),
            ('L', 'Lunes'),
            ('M', 'Martes'),
            ('W', 'Miércoles'),
            ('J', 'Jueves'),
            ('V', 'Viernes'),
            ('S', 'Sábado'),
            ('D', 'Domingo'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # HISTORIA 2: Filtro por docente
    profesor = forms.ModelChoiceField(
        queryset=Profesor.objects.filter(activo=True),
        required=False,
        label='Docente',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Todos los docentes'
    )