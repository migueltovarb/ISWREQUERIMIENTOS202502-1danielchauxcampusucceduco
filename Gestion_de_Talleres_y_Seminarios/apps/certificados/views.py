# apps/certificados/views.py
from django.http import HttpResponse

def index(request):
    return HttpResponse("Página principal de certificados")
      # Alternatively, you can render a template if needed