from datetime import datetime
import locale

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import *
from matriculas.models import *
from matriculas.forms import *
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, HttpResponse, redirect
from django.contrib import messages
from django.http import JsonResponse
from xhtml2pdf import pisa
from django.template.loader import get_template 
import os
from django.contrib.staticfiles import finders
from matriculas.views.admin import SoloAdminMixin
from django.db.models import Max

def link_callback(uri, rel):
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = finders.find(uri.replace(settings.STATIC_URL, ""))
    else:
        return uri
    if not os.path.isfile(path):
        raise Exception(f'Media URI inválido: {path}')
    return path

# Vistas para Matrículas
class MatriculaListView(LoginRequiredMixin, ListView):
    model = Matricula
    template_name = 'matriculas/matriculas/matricula_list.html'
    context_object_name = 'matriculas'
    paginate_by = 200

    def get_queryset(self):
        queryset = super().get_queryset()
        
        search_query = self.request.GET.get('search')
        grado_filtro = self.request.GET.get('grado')
        fondo_filtro = self.request.GET.get('fondo')
        if search_query:
            queryset = queryset.filter(
                models.Q(alumno__nombres_completos__icontains=search_query) |
                models.Q(codigo__icontains=search_query)
            )

        if grado_filtro:
            queryset = queryset.filter(alumno__grado_estudios=grado_filtro)

        if fondo_filtro == 'true':
            queryset = queryset.filter(alumno__fondo_social=True)

        return queryset.order_by('-fecha_matricula')

class MatriculaCreateView(LoginRequiredMixin, CreateView):
    model = Matricula
    form_class = MatriculaForm
    template_name = 'matriculas/matriculas/matricula_form.html'
    success_url = reverse_lazy('matriculas:matricula_list')

    def dispatch(self, request, *args, **kwargs):
        self.alumno_id = request.GET.get('alumno_id')
        self.alumno = None
        if self.alumno_id:
            self.alumno = get_object_or_404(Alumno, pk=self.alumno_id)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.alumno:
            initial['alumno'] = self.alumno
            # Obtener primer apoderado si existe
            apoderado = self.alumno.apoderados.first()
            if apoderado:
                initial['apoderado'] = apoderado
            # Código generado automáticamente
            initial['codigo'] = CodigoManager.generar_codigo_matricula(self.alumno.codigo)
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.alumno:
            try:
                form.fields['alumno'].queryset = Alumno.objects.filter(models.Q(activo=True) | models.Q(pk=self.alumno.pk))
            except Exception:
                form.fields['alumno'].queryset = Alumno.objects.filter(pk=self.alumno.pk)

            form.fields['alumno'].initial = self.alumno

            apoderado = self.alumno.apoderados.first()
            if apoderado:
                form.fields['apoderado'].initial = apoderado
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['monto_form'] = MontoCuotasForm(self.request.POST)
        else:
            initial = {'cuotas': 1}
            context['monto_form'] = MontoCuotasForm(initial=initial)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        monto_form = context['monto_form']
        
        if not monto_form.is_valid():
            return self.render_to_response(self.get_context_data(form=form, monto_form=monto_form))
        
        matricula = form.save(commit=False)
        matricula.usuario_registro = self.request.user
        
        # Calcular montos
        montos = []
        for i in range(1, int(monto_form.cleaned_data['cuotas']) + 1):
            montos.append(float(monto_form.cleaned_data[f'monto_cuota_{i}']))
        
        matricula.monto = sum(montos)
        matricula.cuotas = monto_form.cleaned_data['cuotas']
        matricula.save()

        # Crear pagos
        for i, monto in enumerate(montos, start=1):
            Pago.objects.create(
                matricula=matricula,
                numero_cuota=i,
                tipo_pago='cuota',
                monto_programado=monto_form.cleaned_data[f'monto_cuota_{i}'],
                fecha_vencimiento = monto_form.cleaned_data[f'fecha_cuota_{i}'],
                estado='pendiente',
                usuario_registro=self.request.user
            )

        messages.success(self.request, f'Matrícula "{matricula.codigo}" registrada exitosamente.')
        return redirect('matriculas:matricula_detail', pk=matricula.pk)

class MatriculaUpdateView(LoginRequiredMixin, SoloAdminMixin, UpdateView):
    model = Matricula
    form_class = MatriculaForm
    template_name = 'matriculas/matriculas/matricula_form.html'
    success_url = reverse_lazy('matriculas:matricula_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['monto_form'] = MontoCuotasForm(self.request.POST)
        else:
            # Preparar valores iniciales con TODOS los datos
            initial = {'cuotas': self.object.cuotas}
            pagos = self.object.pagos.order_by('numero_cuota')
            
            for i, pago in enumerate(pagos, start=1):
                initial[f'monto_cuota_{i}'] = pago.monto_programado
                initial[f'fecha_cuota_{i}'] = pago.fecha_vencimiento
            
            # Pasar initial al formulario
            context['monto_form'] = MontoCuotasForm(initial=initial)
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        monto_form = context['monto_form']
        
        if not monto_form.is_valid():
            return self.render_to_response(self.get_context_data(form=form, monto_form=monto_form))
        
        nuevas_cuotas_total = int(monto_form.cleaned_data['cuotas'])
        
        pagos_existentes = self.object.pagos.all()
        pagos_pagados = pagos_existentes.filter(estado='pagado')
        
        max_cuota_pagada = pagos_pagados.aggregate(Max('numero_cuota'))['numero_cuota__max'] or 0
        if nuevas_cuotas_total < max_cuota_pagada:
            messages.error(self.request, f'No puedes reducir a {nuevas_cuotas_total} cuotas porque la cuota #{max_cuota_pagada} ya está pagada.')
            return self.render_to_response(self.get_context_data(form=form, monto_form=monto_form))

        for pago in pagos_pagados:
            nuevo_monto = float(monto_form.cleaned_data.get(f'monto_cuota_{pago.numero_cuota}', 0))
            if pago.numero_cuota <= nuevas_cuotas_total and nuevo_monto != pago.monto_programado:
                 messages.error(self.request, f'La cuota #{pago.numero_cuota} ya está PAGADA. No puedes cambiar su monto (Programado: {pago.monto_programado} vs Nuevo: {nuevo_monto}).')
                 return self.render_to_response(self.get_context_data(form=form, monto_form=monto_form))

        matricula = form.save(commit=False)
        
        montos = []
        for i in range(1, nuevas_cuotas_total + 1):
            montos.append(float(monto_form.cleaned_data[f'monto_cuota_{i}']))
        
        matricula.monto = sum(montos)
        matricula.cuotas = nuevas_cuotas_total
        matricula.save()

        pagos_dict = {p.numero_cuota: p for p in pagos_existentes}

        for i in range(1, nuevas_cuotas_total + 1):
            monto = float(monto_form.cleaned_data[f'monto_cuota_{i}'])
            fecha = monto_form.cleaned_data[f'fecha_cuota_{i}']

            if i in pagos_dict:
                pago_actual = pagos_dict[i]
                
                if pago_actual.estado == 'pagado':

                    pago_actual.fecha_vencimiento = fecha
                    pago_actual.save()
                else:
                    pago_actual.monto_programado = monto
                    pago_actual.fecha_vencimiento = fecha
                    pago_actual.save()
            else:
                Pago.objects.create(
                    matricula=matricula,
                    numero_cuota=i,
                    tipo_pago='cuota',
                    monto_programado=monto,
                    fecha_vencimiento=fecha,
                    estado='pendiente',
                    usuario_registro=self.request.user
                )

        pagos_a_borrar = pagos_existentes.filter(numero_cuota__gt=nuevas_cuotas_total, estado='pendiente')
        pagos_a_borrar.delete()

        messages.success(self.request, 'Matrícula y cronograma actualizados correctamente.')
        return redirect('matriculas:matricula_list')

class MatriculaDetailView(LoginRequiredMixin, DetailView):
    model = Matricula
    template_name = 'matriculas/matriculas/matricula_detail.html'
    context_object_name = 'matricula'

class MatriculaDeleteView(LoginRequiredMixin, SoloAdminMixin, DeleteView):
    model = Matricula
    success_url = reverse_lazy('matriculas:matricula_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return JsonResponse({'success': True})

def ficha_matricula_pdf(request, pk):
    matricula = get_object_or_404(Matricula, uuid=pk)

    pagos = matricula.pagos.all()
    template_path = 'matriculas/matriculas/ficha_matricula_pdf.html'
    context = {
        'matricula': matricula,
        'pagos': pagos
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="ficha_matricula_{matricula.codigo}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)

    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)

    return response

def generar_constancia_pdf(request, alumno_id):
    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        return HttpResponse("Alumno no encontrado", status=404)

    matricula = alumno.matriculas.filter(estado='activa').first()

    if not matricula:
        return HttpResponse("El alumno no tiene matrícula activa", status=400)

    ciclo_obj = matricula.ciclo

    # 🔥 1. TIPO DE CICLO (ajústalo según tu modelo)
    if hasattr(alumno, 'grado') and alumno.grado in ['1ro', '2do', '3ro', '4to', '5to']:
        tipo_ciclo = "Ciclo Escolar"
    else:
        tipo_ciclo = "Ciclo Preuniversitario"

    ciclo_texto = f"{tipo_ciclo} {ciclo_obj.nombre}"

    MESES = {
        1: "enero",
        2: "febrero",
        3: "marzo",
        4: "abril",
        5: "mayo",
        6: "junio",
        7: "julio",
        8: "agosto",
        9: "septiembre",
        10: "octubre",
        11: "noviembre",
        12: "diciembre",
    }

    mes_inicio = MESES[ciclo_obj.fecha_inicio.month]
    mes_fin = MESES[ciclo_obj.fecha_fin.month]
    anio = ciclo_obj.fecha_fin.strftime("%Y")

    texto_fechas = f"iniciando en el mes de {mes_inicio} y culminando en el mes de {mes_fin} del {anio}"

    template = get_template("matriculas/matriculas/constancia.html")

    context = {
        "alumno": alumno,
        "dni": alumno.dni,
        "fecha": datetime.now().strftime("%d/%m/%Y"),

        # 🔥 nuevos datos
        "ciclo_texto": ciclo_texto,
        "texto_fechas": texto_fechas,

        # imágenes (si aún las usas)
        "firma_path": os.path.join(settings.MEDIA_ROOT, "Firma.jpeg"),
        "logo_path": os.path.join(settings.MEDIA_ROOT, "Logo2.png"),
        "pie_path": os.path.join(settings.MEDIA_ROOT, "PiePage.png"),
    }

    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="constancia_{alumno.dni}.pdf"'

    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
        link_callback=link_callback
    )

    if pisa_status.err:
        return HttpResponse("Error generando PDF", status=500)

    return response