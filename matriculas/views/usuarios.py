from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.shortcuts import render
from matriculas.models import *
from django.views.generic import *
from matriculas.forms import *
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

#usuarios
class CustomLoginView(LoginView):
    template_name = 'matriculas/admin/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()

        perfil = getattr(user, 'perfil', None)

        if user.is_superuser or user.is_staff:
             return super().form_valid(form)

        if perfil and perfil.tipo in ['admin', 'usuario']:
            return super().form_valid(form)
        else:
            messages.error(self.request, "No tienes permiso para acceder a este sistema.")
            logout(self.request) 
            return self.form_invalid(form)

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return next_url
        
        return reverse_lazy('matriculas:app_selection')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('matriculas:login')

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'matriculas/admin/password_change_form.html'
    success_url = reverse_lazy('password_change_done')

class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'matriculas/admin/password_change_done.html'

@login_required
def app_selection(request):
    return render(request, 'matriculas/admin/app_selection.html')

@method_decorator(login_required, name='dispatch')
class UsuarioCreateView(CreateView):
    model = User
    form_class = UsuarioCreateForm
    template_name = 'matriculas/admin/usuario_create.html'

    def form_valid(self, form):
        password = form.cleaned_data.get('password')
        usuario = form.save()

        return render(self.request, self.template_name, {
            'form': self.get_form_class()(),
            'password_inicial': password,
            'username': usuario.username
        })

@method_decorator(login_required, name='dispatch')
class UsuarioUpdateView(UpdateView):
    model = User
    form_class = UsuarioUpdateForm
    template_name = 'matriculas/admin/usuario_update.html'
    success_url = reverse_lazy('matriculas:lista_usuarios') 

    def test_func(self):
        return self.request.user.is_superuser or \
               (hasattr(self.request.user, 'perfil') and self.request.user.perfil.tipo == 'admin')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Usuario'
        return context

@method_decorator(login_required, name='dispatch')
class UsuarioListView(ListView):
    model = User
    template_name = 'matriculas/admin/lista_usuarios.html'
    context_object_name = 'usuarios'