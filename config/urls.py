
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from predicciones.cuentas import usuarios

urlpatterns = [
    path("cuenta/usuarios/", usuarios, name="usuarios"),
    path("cuenta/entrar/", auth_views.LoginView.as_view(template_name="predicciones/login.html", redirect_authenticated_user=True), name="login"),
    path("cuenta/salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("", include("predicciones.urls")),
]
