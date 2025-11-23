from django.db import models
from apps.core.models import Usuario  # Si usas Usuario personalizado, si no, usa get_user_model()

class Evaluacion(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.titulo


class Pregunta(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='preguntas')
    texto = models.TextField()

    def __str__(self):
        return f"Pregunta #{self.id} de {self.evaluacion.titulo}"


class Respuesta(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='respuestas')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    respuesta_texto = models.TextField()
    fecha_respuesta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Respuesta de {self.usuario.username} a {self.pregunta.id}"
