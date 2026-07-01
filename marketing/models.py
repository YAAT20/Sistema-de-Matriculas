from django.db import models
from marketing.services.thumbnails import ThumbnailService
from pathlib import Path

class Evento(models.Model):

    ESTADOS = [
        ('planificado', 'Planificado'),
        ('confirmado', 'Confirmado'),
        ('realizado', 'Realizado'),
        ('cancelado', 'Cancelado'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField(db_index=True)
    lugar = models.CharField( max_length=255)
    cantidad_estimada_personas = models.PositiveIntegerField( null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='planificado')
    observaciones = models.TextField( blank=True)
    creado_en = models.DateTimeField(auto_now_add=True )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return self.nombre
    
class FotoEvento(models.Model):

    evento = models.ForeignKey(Evento,on_delete=models.CASCADE,related_name='fotos')
    imagen = models.ImageField( upload_to='marketing/eventos/fotos/')
    descripcion = models.CharField( max_length=255, blank=True)
    fecha_captura = models.DateTimeField( null=True, blank=True)
    orden = models.PositiveIntegerField(default=1)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto de Evento'
        verbose_name_plural = 'Fotos de Eventos'
        ordering = ['orden']

    def __str__(self):
        return self.descripcion or f'Foto {self.pk}'
    
class Publicacion(models.Model):

    ESTADOS = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('publicada', 'Publicada'),
        ('archivada', 'Archivada'),
    ]

    titulo = models.CharField(max_length=255)
    evento = models.ForeignKey(Evento,null=True,blank=True,on_delete=models.SET_NULL, related_name='publicaciones')
    estado = models.CharField(max_length=20,choices=ESTADOS,default='borrador')
    fecha_programada = models.DateTimeField(null=True,blank=True, db_index=True)
    fecha_publicacion = models.DateTimeField(null=True,blank=True, db_index=True)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering = ['-creado_en']

    def __str__(self):
        return self.titulo

    @property
    def primer_archivo(self):
        archivos = list(self.archivos.all())
        return archivos[0] if archivos else None

    @property
    def cantidad_archivos(self):
        return len(self.archivos.all())

    @property
    def plataformas(self):
        return self.copies.all()

    @property
    def estado_color(self):

        colores = {
            "borrador": "bg-gray-100 text-gray-700",
            "pendiente": "bg-yellow-100 text-yellow-700",
            "aprobada": "bg-blue-100 text-blue-700",
            "publicada": "bg-green-100 text-green-700",
            "archivada": "bg-red-100 text-red-700",
        }

        return colores.get(
            self.estado,
            "bg-gray-100 text-gray-700"
        )
    
class CopyPublicacion(models.Model):

    PLATAFORMAS = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('whatsapp', 'WhatsApp'),
        ('tiktok', 'TikTok'),
    ]

    publicacion = models.ForeignKey(Publicacion,on_delete=models.CASCADE,related_name='copies')
    plataforma = models.CharField(max_length=20,choices=PLATAFORMAS)
    copy = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['publicacion', 'plataforma'],
                name='unique_publicacion_plataforma'
            )
        ]
        verbose_name = 'Copy'
        verbose_name_plural = 'Copies'

    def __str__(self):
        return f'{self.publicacion} - {self.plataforma}'
    
class ArchivoPublicacion(models.Model):

    publicacion = models.ForeignKey(Publicacion,on_delete=models.CASCADE,related_name="archivos"    )
    archivo = models.FileField(upload_to="marketing/publicaciones/")
    thumbnail = models.ImageField(upload_to="marketing/publicaciones/thumbnails/",null=True,blank=True)
    descripcion = models.CharField(max_length=255, blank=True)
    orden = models.PositiveIntegerField(default=1)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Archivo de Publicación"
        verbose_name_plural = "Archivos de Publicaciones"
        ordering = ["orden"]

    def __str__(self):
        return self.descripcion or f"Archivo {self.pk}"

    def save(self, *args, **kwargs):
        print("SAVE ArchivoPublicacion")
        archivo_nuevo = self._state.adding
        super().save(*args, **kwargs)
        if (
            archivo_nuevo
            and not self.thumbnail
            and self.tipo == "imagen"
        ):
            print("Generando thumbnail...")
            ThumbnailService.generar(self)
            super().save(update_fields=["thumbnail"])
            
    @property
    def extension(self):
        return Path(self.archivo.name).suffix.lower()

    @property
    def tipo(self):

        imagenes = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".svg",
        }

        videos = {
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm",
            ".m4v",
        }

        documentos = {
            ".pdf",
        }

        if self.extension in imagenes:
            return "imagen"

        if self.extension in videos:
            return "video"

        if self.extension in documentos:
            return "pdf"

        return "archivo"

class RecursoMarketing(models.Model):

    CATEGORIAS = [
        ('logo', 'Logo'),
        ('plantilla', 'Plantilla'),
        ('video', 'Video'),
        ('imagen', 'Imagen'),
        ('musica', 'Música'),
        ('documento', 'Documento'),
        ('otro', 'Otro'),
    ]

    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=20,choices=CATEGORIAS)
    archivo = models.FileField(upload_to='marketing/recursos/')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recurso de Marketing'
        verbose_name_plural = 'Recursos de Marketing'
        ordering = ['-creado_en']

    def __str__(self):
        return self.nombre  
    
    @property
    def extension(self):
        return self.archivo.name.split(".")[-1].lower()