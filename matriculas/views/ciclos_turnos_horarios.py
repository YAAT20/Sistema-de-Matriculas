from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import *
from matriculas .models import *
from matriculas.forms import *
from django.contrib import messages
from django.urls import reverse, reverse_lazy

# Vistas para Configuración (Ciclos, Turnos, Horarios)
class CicloListView(LoginRequiredMixin, ListView):
    model = Ciclo
    template_name = 'matriculas/ciclos/ciclo_list.html'
    context_object_name = 'ciclos'

class CicloCreateView(LoginRequiredMixin, CreateView ):
    model = Ciclo
    form_class = CicloForm
    template_name = 'matriculas/ciclos/ciclo_form.html'
    success_url = reverse_lazy('matriculas:ciclo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ciclo creado exitosamente')
        return super().form_valid(form)

class CicloUpdateView(LoginRequiredMixin, UpdateView):
    model = Ciclo
    form_class = CicloForm
    template_name = 'matriculas/ciclos/ciclo_form.html'
    success_url = reverse_lazy('matriculas:ciclo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Ciclo actualizado exitosamente')
        return super().form_valid(form)

class TurnoListView(LoginRequiredMixin, ListView):
    model = Turno
    template_name = 'matriculas/turno/turno_list.html'
    context_object_name = 'turnos'

class TurnoCreateView(LoginRequiredMixin, CreateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'matriculas/turno/turno_form.html'
    success_url = reverse_lazy('matriculas:turno_list')

    def form_valid(self, form):
        messages.success(self.request, 'Turno creado exitosamente')
        return super().form_valid(form)

class TurnoUpdateView(LoginRequiredMixin, UpdateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'matriculas/turno/turno_form.html'
    success_url = reverse_lazy('matriculas:turno_list')

    def form_valid(self, form):
        messages.success(self.request, 'Turno actualizado exitosamente')
        return super().form_valid(form)

class HorarioListView(LoginRequiredMixin, ListView):
    model = Horario
    template_name = 'matriculas/horarios/horario_list.html'
    context_object_name = 'horarios'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(nombre__icontains=search) |
                models.Q(dias_bloque1__icontains=search) |
                models.Q(dias_bloque2__icontains=search)
            )
        return queryset.order_by('hora_inicio1')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class HorarioCreateView(LoginRequiredMixin, CreateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'matriculas/horarios/horario_form.html'
    success_url = reverse_lazy('matriculas:horario_list')


    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Horario "{self.object.nombre}" creado exitosamente'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Horario'
        return context

class HorarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'matriculas/horarios/horario_form.html'
    success_url = reverse_lazy('matriculas:horario_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Horario "{self.object.nombre}" actualizado exitosamente'
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Horario: {self.object.nombre}'
        return context

class HorarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Horario
    template_name = 'matriculas/horarios/horario_confirm_delete.html'
    success_url = reverse_lazy('matriculas:horario_list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            f'Horario "{self.object.nombre}" eliminado exitosamente'
        )
        return response