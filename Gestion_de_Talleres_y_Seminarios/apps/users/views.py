from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse


# Vista Home para probar que la app funciona
def home(request):
    return HttpResponse("Users app funcionando correctamente")


# --------------------------
# AUTENTICACIÓN
# --------------------------

def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "users/login.html")


def logout_user(request):
    logout(request)
    return redirect("login")


# --------------------------
# REGISTRO DE USUARIOS
# --------------------------

def register_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe.")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Usuario registrado correctamente.")
            return redirect("login")

    return render(request, "users/register.html")
