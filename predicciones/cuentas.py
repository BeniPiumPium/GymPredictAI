from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

class CrearUsuarioForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email')

@user_passes_test(lambda user: user.is_active and user.is_superuser)
@require_http_methods(['GET', 'POST'])
def usuarios(request):
    form = CrearUsuarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuario creado. Ya puede iniciar sesión en este gimnasio.')
        return redirect('usuarios')
    return render(request, 'predicciones/usuarios.html', {'formulario': form, 'usuarios': get_user_model().objects.order_by('username')})
