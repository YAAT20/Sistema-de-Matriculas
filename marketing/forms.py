from django import forms
from marketing.models import *
from django.forms import inlineformset_factory

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'lugar', 'cantidad_estimada_personas', 'estado', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300'}),
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'w-full rounded-lg border-gray-300'}),
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full rounded-lg border-gray-300'}),
            'lugar': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300'}),
            'cantidad_estimada_personas': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300'}),
            'estado': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300'}),
            'observaciones': forms.Textarea(attrs={'rows': 4, 'class': 'w-full rounded-lg border-gray-300'}),
        }

class FotoEventoForm(forms.ModelForm):
    class Meta:
        model = FotoEvento
        fields = ['imagen', 'descripcion', 'fecha_captura', 'orden']

class SubirFotosEventoForm(forms.Form):
    imagenes = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'block w-full border rounded-lg p-2'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['imagenes'].widget.attrs.update({'multiple': True})
        
#PUBLICACIONES
class PublicacionForm(forms.ModelForm):
    class Meta:
        model = Publicacion
        fields = [
            'titulo', 'evento', 'alcance', 'estado', 'fecha_programada', 'fecha_publicacion', 'observaciones',
            #'titulo', 'evento', 'alcance', 'estado', 'fecha_programada', 'fecha_publicacion', 'observaciones',
            
        ]

        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 px-2 py-2'
            }),
            'evento': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 px-2 py-2'
            }),
            'alcance': forms.Select(attrs={
                'class': 'w-full rounded-xl border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 shadow-sm transition-all focus:border-blue-500 focus:bg-white',
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 px-2 py-2'
            }),
            'fecha_programada': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 px-2 py-2'
            }),
            'fecha_publicacion': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 px-2 py-2'
            }),
            'observaciones': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full rounded-lg border-gray-300 focus:ring-blue-500 focus:border-blue-500 px-2 py-2'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for campo in ['fecha_programada', 'fecha_publicacion']:
            if self.instance.pk:
                valor = getattr(self.instance, campo)
                if valor:
                    self.initial[campo] = valor.strftime('%Y-%m-%dT%H:%M')

class CopyPublicacionForm(forms.ModelForm):

    class Meta:
        model = CopyPublicacion
        fields = [
            'plataforma','titulo','texto_principal','copy'
        ]
        widgets = {
            'plataforma': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 px-2 py-2' 
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 px-2 py-2'
            }),
            'texto_principal': forms.Textarea(attrs={
                'rows': 1,
                'class': 'w-full rounded-lg border-gray-300 p-3'
            }),
            'copy': forms.Textarea(attrs={
                'rows': 16,
                'class': 'w-full rounded-lg border-gray-300 p-3'
            }),
        }

class ArchivoPublicacionForm(forms.ModelForm):
    class Meta:
        model = ArchivoPublicacion
        fields = [
            'archivo','descripcion','orden'
        ]
        widgets = {
            'archivo': forms.ClearableFileInput(attrs={
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer focus:outline-none'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 px-4 py-2'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 px-4 py-2'
            }),
        }

CopyFormSet = inlineformset_factory(
    parent_model=Publicacion,
    model=CopyPublicacion,
    form=CopyPublicacionForm,
    extra=0,
    can_delete=True
)

ArchivoFormSet = inlineformset_factory(
    parent_model=Publicacion,
    model=ArchivoPublicacion,
    form=ArchivoPublicacionForm,
    extra=0,
    can_delete=True
)

class RecursoMarketingForm(forms.ModelForm):
    class Meta:
        model = RecursoMarketing
        fields = ['nombre', 'descripcion', 'categoria', 'archivo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'archivo':
                field.widget.attrs.update({
                    'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})
            else:
                field.widget.attrs.update({
                    'class': 'w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm'})