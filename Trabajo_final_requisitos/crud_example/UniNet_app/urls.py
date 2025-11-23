# ============================================================================
# UNINET - PLATAFORMA DE INSCRIPCIÓN A CURSOS UNIVERSITARIOS
# CONFIGURACIÓN DE URLS - urls.py
# ============================================================================

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ========================================================================
    # RUTAS PÚBLICAS
    # ========================================================================
    path('', views.home_view, name='home'),
    path('registro/', views.registro_estudiante, name='registro_estudiante'),
    
    # ========================================================================
    # AUTENTICACIÓN
    # ========================================================================
    path('login/', auth_views.LoginView.as_view(
        template_name='UniNet_app/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='home'
    ), name='logout'),
    
    # ========================================================================
    # RUTAS DE ESTUDIANTES
    # ========================================================================
    path('cursos/', views.cursos_list, name='cursos_list'),
    path('inscribir/<int:horario_id>/', views.inscribir_curso, name='inscribir_curso'),
    path('mis-inscripciones/', views.mis_inscripciones, name='mis_inscripciones'),
    path('cancelar-inscripcion/<int:inscripcion_id>/', views.cancelar_inscripcion, name='cancelar_inscripcion'),
    path('pago/<int:inscripcion_id>/', views.procesar_pago, name='procesar_pago'),
    
    # ========================================================================
    # RUTAS DE ADMINISTRACIÓN - CURSOS
    # ========================================================================
    path('admin/cursos/', views.cursos_admin_list, name='cursos_admin_list'),
    path('admin/cursos/crear/', views.curso_create, name='curso_create'),
    path('admin/cursos/editar/<int:id>/', views.curso_update, name='curso_update'),
    path('admin/cursos/eliminar/<int:id>/', views.curso_delete, name='curso_delete'),
    
    # ========================================================================
    # RUTAS DE ADMINISTRACIÓN - HORARIOS
    # ========================================================================
    path('admin/horarios/', views.horarios_admin_list, name='horarios_admin_list'),
    path('admin/horarios/crear/', views.horario_create, name='horario_create'),
    path('admin/horarios/editar/<int:id>/', views.horario_update, name='horario_update'),
    path('admin/horarios/eliminar/<int:id>/', views.horario_delete, name='horario_delete'),
    
    # ========================================================================
    # RUTAS DE ADMINISTRACIÓN - PROFESORES
    # ========================================================================
    path('admin/profesores/', views.profesores_admin_list, name='profesores_admin_list'),
    path('admin/profesores/crear/', views.profesor_create, name='profesor_create'),
    path('admin/profesores/editar/<int:id>/', views.profesor_update, name='profesor_update'),
    path('admin/profesores/eliminar/<int:id>/', views.profesor_delete, name='profesor_delete'),
    
    # ========================================================================
    # RUTAS DE ADMINISTRACIÓN - PERIODOS
    # ========================================================================
    path('admin/periodos/', views.periodos_admin_list, name='periodos_admin_list'),
    path('admin/periodos/crear/', views.periodo_create, name='periodo_create'),
    path('admin/periodos/editar/<int:id>/', views.periodo_update, name='periodo_update'),
    
    # ========================================================================
    # RUTAS DE ADMINISTRACIÓN - DASHBOARD Y REPORTES
    # ========================================================================
    path('admin/dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('admin/reportes/', views.reportes_view, name='reportes_view'),
]