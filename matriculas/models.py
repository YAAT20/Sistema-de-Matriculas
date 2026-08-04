from django.db import models, transaction
from django.db.models import Max
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Max, IntegerField
from django.db.models.functions import Substr, Cast
from django.conf import settings
import uuid

class Ciclo(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del ciclo")
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de finalización")
    activo = models.BooleanField(default=True, verbose_name="Ciclo activo")
    turnos = models.ManyToManyField('Turno', related_name='ciclos', verbose_name="Turnos disponibles")

    class Meta:
        verbose_name = "Ciclo"
        verbose_name_plural = "Ciclos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
    def finalizar_ciclo(self):
        with transaction.atomic():
            matriculas_activas = self.matricula_set.filter(estado='activa')

            for matricula in matriculas_activas:
                matricula.estado = 'finalizada'
                matricula.save()

            self.activo = False
            self.save()

        return True

    @classmethod
    def verificar_ciclos_finalizados(cls):

        hoy = timezone.now().date()
        ciclos_a_finalizar = cls.objects.filter(
            activo=True,
            fecha_fin__lte=hoy
        )
        for ciclo in ciclos_a_finalizar:
            ciclo.finalizar_ciclo()
            
        return ciclos_a_finalizar.count()

class Horario(models.Model):
    DIAS_SEMANA = [
        ('L', 'Lunes'),
        ('M', 'Martes'),
        ('Mi', 'Miércoles'),
        ('J', 'Jueves'),
        ('V', 'Viernes'),
        ('S', 'Sábado'),
        ('D', 'Domingo'),
    ]

    nombre = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre del horario",
        help_text="Ej: Turno Mañana, Grupo Intensivo"
    )

    hora_inicio1 = models.TimeField(null=True, blank=True)
    hora_fin1 = models.TimeField(null=True, blank=True)
    dias_bloque1 = models.CharField(max_length=50)
    hora_inicio2 = models.TimeField(null=True, blank=True)
    hora_fin2 = models.TimeField(null=True, blank=True)
    dias_bloque2 = models.CharField(max_length=50, blank=True)

    def get_dias_bloque1_display(self):
        dias_dict = dict(self.DIAS_SEMANA)
        return ', '.join([dias_dict.get(d, d) for d in self.dias_bloque1.split(',') if d])

    def get_dias_bloque2_display(self):
        if not self.dias_bloque2:
            return ''
        dias_dict = dict(self.DIAS_SEMANA)
        return ', '.join([dias_dict.get(d, d) for d in self.dias_bloque2.split(',') if d])

    def clean(self):
        errores = {}

        if any([self.hora_inicio2, self.hora_fin2, self.dias_bloque2]):
            if not all([self.hora_inicio2, self.hora_fin2, self.dias_bloque2]):
                errores['hora_inicio2'] = "Si especifica un segundo bloque horario, debe completar todos sus campos"

        if self.hora_inicio1 and self.hora_fin1:
            if self.hora_fin1 <= self.hora_inicio1:
                errores['hora_fin1'] = "La hora de fin debe ser posterior a la hora de inicio en el Bloque 1"

        if self.hora_inicio2 and self.hora_fin2:
            if self.hora_fin2 <= self.hora_inicio2:
                errores['hora_fin2'] = "La hora de fin debe ser posterior a la hora de inicio en el Bloque 2"

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        bloques = []
        if self.hora_inicio1 and self.hora_fin1:
            bloques.append(f"{self.hora_inicio1.strftime('%H:%M')}-{self.hora_fin1.strftime('%H:%M')} ({self.dias_bloque1})")
        if self.hora_inicio2 and self.hora_fin2:
            bloques.append(f"{self.hora_inicio2.strftime('%H:%M')}-{self.hora_fin2.strftime('%H:%M')} ({self.dias_bloque2})")

        bloques_str = " | ".join(bloques) if bloques else "Sin horario definido"
        return f"{self.nombre} - {bloques_str}"

class Turno(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del turno")

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class CodigoManager:
    @staticmethod
    def generar_codigo_alumno(grado_estudios, fondo_social=False):
        grado_map = {
            'pre': 'RP6',
            '5s': 'RS5',
            '4s': 'RS4',
            '3s': 'RS3',
            '2s': 'RS2',
            '1s': 'RS1',
            '6p': 'EP6',
            '5p': 'EP5',
        }

        base_prefijo = grado_map.get(grado_estudios, 'RSX')

        if fondo_social:
            prefijo = base_prefijo[:2] + 'F' + base_prefijo[2:]
            digitos = 2 
        else:
            prefijo = base_prefijo
            digitos = 3

        sufijo_max = (
            Alumno.objects
            .filter(codigo__regex=rf'^{prefijo}\d+$')
            .annotate(
                num_sufijo=Cast(Substr('codigo', len(prefijo) + 1), IntegerField())
            )
            .aggregate(Max('num_sufijo'))['num_sufijo__max']
        )

        numero = (sufijo_max or 0) + 1

        return f"{prefijo}{numero:0{digitos}d}"

    @staticmethod
    def generar_codigo_apoderado(codigo_alumno):
        if 'F' in codigo_alumno[:4]:
            if codigo_alumno.startswith('RPF'):
                return f"APF{codigo_alumno[3:]}"
            elif codigo_alumno.startswith('RSF'):
                return f"ASF{codigo_alumno[3:]}"
            elif codigo_alumno.startswith('EPF'):
                return f"AEF{codigo_alumno[3:]}"
        
        # Casos Regulares
        if codigo_alumno.startswith('RP'):
            return f"AP{codigo_alumno[2:]}"
        elif codigo_alumno.startswith(('RS', 'EP')):
            return f"AS{codigo_alumno[2:]}"
        
        return f"AX{codigo_alumno[2:]}"

    @staticmethod
    def generar_codigo_matricula(codigo_alumno):
        es_fondo = 'F' in codigo_alumno[:4]

        if es_fondo:
            numero = codigo_alumno[3:]
        else:
            numero = codigo_alumno[2:]

        if codigo_alumno.startswith('RP'):
            prefijo = 'MPF' if es_fondo else 'MP'
        elif codigo_alumno.startswith(('RS', 'EP')):
            prefijo = 'MSF' if es_fondo else 'MS'
        else:
            prefijo = 'MXF' if es_fondo else 'MX'

        codigo_base = f"{prefijo}{numero}"
        codigo_final = codigo_base
        contador = 1
        while Matricula.objects.filter(codigo=codigo_final).exists():
            contador += 1
            codigo_final = f"{codigo_base}-{contador}"

        return codigo_final

class Alumno(models.Model):
    GRADO_OPCIONES = [
        ('5p', '5to de primaria'),
        ('6p', '6to de primaria'),
        ('1s', '1ro de secundaria'),
        ('2s', '2do de secundaria'),
        ('3s', '3ro de secundaria'),
        ('4s', '4to de secundaria'),
        ('5s', '5to de secundaria'),
        ('pre', 'Preuniversitario'),
    ]

    SEXO_OPCIONES = [('M', 'Masculino'), ('F', 'Femenino')]

    codigo = models.CharField(max_length=10, unique=True, blank=True, editable=False)
    grado_estudios = models.CharField(max_length=30, choices=GRADO_OPCIONES)
    nombres_completos = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)
    sexo = models.CharField(max_length=1, choices=SEXO_OPCIONES)
    celular_llamadas = models.CharField(max_length=9)
    numero_whatsapp = models.CharField(max_length=9)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    colegio_de_procedencia = models.CharField(max_length=100, blank=True, null=True)
    carrera_tentativa = models.CharField(max_length=100, blank=True, null=True)
    foto_previa = models.ImageField(upload_to="alumnos/fotos_previas/", blank=True, null=True)
    foto_frente = models.ImageField(upload_to="alumnos/fotos_frente/", blank=True, null=True)
    foto_lado = models.ImageField(upload_to="alumnos/fotos_lado/", blank=True, null=True)
    foto_corte = models.ImageField(upload_to="alumnos/fotos_corte/", blank=True, null=True)
    sexo_data = models.CharField(max_length=10, choices=[('hija', 'hija'), ('hijo', 'hijo')], blank=True)
    direccion_alumno = models.TextField(max_length=150, blank=True, null=True)
    fondo_social = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ['codigo']

    def save(self, *args, **kwargs):
        if self.sexo == 'M':
            self.sexo_data = 'hijo'
        elif self.sexo == 'F':
            self.sexo_data = 'hija'
        else:
            self.sexo_data = ''

        if self.pk:
            original = Alumno.objects.get(pk=self.pk)
            if (
                original.grado_estudios != self.grado_estudios or
                original.fondo_social != self.fondo_social
            ):
                self.codigo = CodigoManager.generar_codigo_alumno(
                    self.grado_estudios,
                    self.fondo_social
                )
        else:
            if not self.codigo:
                self.codigo = CodigoManager.generar_codigo_alumno(
                    self.grado_estudios,
                    self.fondo_social
                )
            self.activo = False

        if Alumno.objects.filter(codigo=self.codigo).exclude(pk=self.pk).exists():
            raise ValidationError({'codigo': 'Este código ya está en uso'})

        super().save(*args, **kwargs)
        self.actualizar_codigos_relacionados()

    def actualizar_codigos_relacionados(self):
        for matricula in self.matriculas.all():
            nuevo_codigo = CodigoManager.generar_codigo_matricula(self.codigo)
            if matricula.codigo != nuevo_codigo:
                matricula.codigo = nuevo_codigo
                matricula.save()

    def get_absolute_url(self):
        return reverse('alumno_detail', args=[str(self.id)])

    def __str__(self):
        return f"{self.codigo} - {self.nombres_completos}"

    def actualizar_estado(self):
        tiene_matriculas_activas = self.matriculas.filter(estado='activa').exists()

        if self.activo != tiene_matriculas_activas:
            self.activo = tiene_matriculas_activas
            self.save(update_fields=['activo'])

class Apoderado(models.Model):
    PARENTESCO_CHOICES = [
        ('Padre', 'Padre'), ('Madre', 'Madre'), ('Hermano', 'Hermano'), ('Hermana', 'Hermana'),
        ('Tio', 'Tío'), ('Tia', 'Tía'), ('Primo', 'Primo'), ('Prima', 'Prima'),
        ('Abuelo', 'Abuelo'), ('Abuela', 'Abuela'),
    ]
    ABREVIATURA_CHOICES = [
        ('Señor','Señor',),('Señora', 'Señora')
    ]

    codigo = models.CharField(max_length=10, unique=True, blank=True, editable=False)
    alumnos = models.ManyToManyField(Alumno, related_name='apoderados')
    nombre_completo = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)
    celular = models.CharField(max_length=9)
    direccion = models.TextField(max_length=150, blank=True, null=True)
    parentesco = models.CharField(max_length=10, choices=PARENTESCO_CHOICES)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    abreviatura = models.CharField( max_length= 10, choices=ABREVIATURA_CHOICES)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Apoderado"
        verbose_name_plural = "Apoderados"

    def save(self, *args, **kwargs):
        if not self.codigo and self.alumnos.exists():
            primer_alumno = self.alumnos.order_by('fecha_registro').first()
            self.codigo = CodigoManager.generar_codigo_apoderado(primer_alumno.codigo)

        super().save(*args, **kwargs)

    def actualizar_estado(self):
        tiene_matriculas_activas = Matricula.objects.filter(
            alumno__in=self.alumnos.all(),
            estado='activa'
        ).exists()

        if self.activo != tiene_matriculas_activas:
            self.activo = tiene_matriculas_activas
            self.save(update_fields=['activo'])

    def get_absolute_url(self):
        return reverse('apoderado_detail', args=[str(self.id)])

    def __str__(self):
        return f"{self.codigo} - {self.nombre_completo}"

class Matricula(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'), ('congelada', 'Congelada'), ('finalizada', 'Finalizada'),]
    MODALIDADES = [('presencial', 'Presencial'), ('virtual', 'Virtual'),('mixta', 'Mixta')]
    TIPOS_MATRICULA = [ ('regular', 'REGULAR'), ('promocion', 'PROMOCION'), ('beca50', 'BECA 50%'), ('beca100', 'BECA 100%'), ('fondo_social', 'FONDO SOCIAL'),('exalumno', 'EXALUMNO'),('gerencia', 'GERENCIA')]

    TIPOS_ALUMNO = [
        ('pre_uni_promo', 'Pre Universitario Promoción'),
        ('pre_uni_excelencia', 'Pre Universitario Excelencia'),
        ('pre_uni_provincia', 'Pre Universitario Provincia'),
        ('pre_uni_virtual', 'Pre Universitario Virtual'),
        ('3_4_5_preferente', '3ro, 4to y 5to Preferente'),
        ('1_2_3_basico', '1ro, 2do y 3ro Básico'),
        ('cepunc_manana', 'CEPUNC Mañana'),
        ('cepunc_tarde', 'CEPUNC Tarde')]
    
    tipo_alumno = models.CharField(max_length=20, choices=TIPOS_ALUMNO, default='pre_uni_promo')
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    codigo = models.CharField(max_length=10, unique=True, blank=True, editable=False)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='matriculas')
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    cuotas = models.IntegerField()
    modalidad = models.CharField(max_length=20, choices=MODALIDADES)
    ciclo = models.ForeignKey(Ciclo, on_delete=models.PROTECT)
    turno = models.ForeignKey(Turno, on_delete=models.PROTECT)
    horario = models.ForeignKey(Horario, on_delete=models.PROTECT)
    fecha_matricula = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activa')
    tipo_matricula = models.CharField(max_length=20, choices=TIPOS_MATRICULA, default='regular')
    usuario_registro = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='matriculas_registradas')
    
    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"

    def clean(self):
        if not self.codigo and hasattr(self, 'alumno'):
            self.codigo = CodigoManager.generar_codigo_matricula(self.alumno.codigo)

        if Matricula.objects.filter(codigo=self.codigo).exclude(pk=self.pk).exists():
            raise ValidationError({'codigo': 'Este código ya está en uso'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

        if self.alumno:
            self.alumno.actualizar_estado()

        if self.apoderado:
            self.apoderado.actualizar_estado()

    def delete(self, *args, **kwargs):
        alumno = self.alumno
        apoderado = self.apoderado

        super().delete(*args, **kwargs)

        if alumno:
            alumno.actualizar_estado()

        if apoderado:
            apoderado.actualizar_estado()

    def get_absolute_url(self):
        return reverse('matricula_detail', args=[str(self.id)])

    def __str__(self):
        return f"{self.codigo} - {self.alumno.nombres_completos}"

    def reactivar_para_nuevo_ciclo(self, nuevo_ciclo, nuevo_turno, nuevo_horario, usuario):
        """
        Reactiva una matrícula para un nuevo ciclo
        """
        if self.estado != 'finalizada':
            raise ValidationError("Solo se pueden reactivar matrículas finalizadas")
        if not nuevo_ciclo.activo:
            raise ValidationError("El nuevo ciclo no está activo")
        if nuevo_turno not in nuevo_ciclo.turnos.all():
            raise ValidationError("El turno seleccionado no está disponible en este ciclo")
            
        nueva_matricula = Matricula.objects.create(
            alumno=self.alumno,
            apoderado=self.apoderado,
            monto=self.monto,
            cuotas=self.cuotas,
            modalidad=self.modalidad,
            ciclo=nuevo_ciclo,
            turno=nuevo_turno,
            horario=nuevo_horario,
            estado='activa',
            tipo_alumno=self.tipo_alumno,
            usuario_registro=usuario
        )
        
        return nueva_matricula

# Modelo para guardar el template editable del mensaje de WhatsApp
class MensajeWhatsAppConfig(models.Model):
    nombre = models.CharField(max_length=50, default="Recordatorio de pago")
    template = models.TextField(default="Estimado/a {apoderado}, le recordamos que tiene una cuota pendiente para la matrícula de {alumno} (cuota {numero_cuota}) por S/ {monto} con vencimiento el {fecha_vencimiento}. Por favor, regularice su pago para evitar inconvenientes.")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Pago(models.Model):
    ESTADO_PAGO = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('observado', 'Observado'),
    ]

    TIPO_PAGO = [
        ('cuota', 'Cuota mensual'),
        ('matricula', 'Matrícula'),
        ('otros', 'Otros'),
    ]
    Forma_pago = [
        ('Efectivo', 'Efectivo'),
        ('Yape', 'Yape'),
        ('Transferencia', 'Transferencia bancaria'),
        ('Plin', 'Plin'),
    ]

    forma_pago = models.CharField(max_length=20, choices=Forma_pago, default='Efectivo')
    matricula = models.ForeignKey('Matricula', on_delete=models.CASCADE, related_name='pagos')
    numero_cuota = models.IntegerField(null=True, blank=True)
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO)
    monto_programado = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO, default='pendiente')
    observacion = models.TextField(blank=True)
    usuario_registro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_registrados')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    foto_comprobante = models.FileField(upload_to="pagos/comprobantes/", blank=True, null=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['fecha_vencimiento']
        unique_together = ('matricula', 'numero_cuota', 'tipo_pago')

    def __str__(self):
        cuota_info = f" - Cuota {self.numero_cuota}" if self.numero_cuota else ""
        return f"{self.matricula.codigo}{cuota_info} - {self.get_estado_display()}"

    def save(self, *args, **kwargs):
        if self.estado == 'pendiente':
            self.monto_pagado = 0
            self.fecha_pago = None
        super().save(*args, **kwargs)

    def confirmar_pago(self, monto_pagado, usuario, forma_pago='Efectivo', observacion='', fecha_pago=None):
        self.monto_pagado = monto_pagado
        self.fecha_pago = fecha_pago or timezone.now().date()
        self.estado = 'pagado'
        self.usuario_registro = usuario
        self.forma_pago = forma_pago
        self.observacion = observacion
        self.save()

    def get_whatsapp_url(self):

        from urllib.parse import quote
        config = MensajeWhatsAppConfig.objects.filter(activo=True).first()
        if not config:
            template = (
                "Estimado/a {apoderado}, le recordamos que tiene una cuota pendiente "
                "para la matrícula de {alumno} (cuota {numero_cuota}) por S/ {monto} "
                "con vencimiento el {fecha_vencimiento}. Por favor, regularice su pago para evitar inconvenientes."
            )
        else:
            template = config.template
        
        apoderado = self.matricula.apoderado.nombre_completo
        alumno = self.matricula.alumno.nombres_completos
        numero_cuota = self.numero_cuota or "-"
        monto = self.monto_programado
        fecha_vencimiento = self.fecha_vencimiento.strftime("%d/%m/%Y")

        mensaje = template.format(
            apoderado=apoderado,
            alumno=alumno,
            numero_cuota=numero_cuota,
            monto=monto,
            fecha_vencimiento=fecha_vencimiento
        )

        telefono = self.matricula.apoderado.celular
        mensaje_encoded = quote(mensaje)
        url = f"https://wa.me/51{telefono}?text={mensaje_encoded}"
        return url

class Perfil(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('usuario', 'Usuario'),
        ('marketing', 'Marketing'),
    ]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO_CHOICES, default='usuario')

    def __str__(self):
        return f'{self.user.username} ({self.get_tipo_display()})'

class Seguimiento(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='seguimientos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    texto = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.matricula} - {self.fecha_registro}"

class Simulacro(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    fecha = models.DateField(verbose_name="Fecha")
    costo = models.DecimalField(max_digits=6, decimal_places=2, default=10.00, verbose_name="Costo S/.")
    ciclo = models.ForeignKey(Ciclo, on_delete=models.CASCADE)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, verbose_name="Turno destinado", null=True, blank=True)
    class Meta:
        verbose_name = "Simulacro"
        verbose_name_plural = "Simulacros"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.nombre} - {self.turno.nombre if self.turno else 'Sin turno'}"

    @property
    def ganancia(self):
        pagantes = self.asistencias.filter(pago='si').count()
        return pagantes * self.costo

    @property
    def total_fondo(self):
        becados = self.asistencias.filter(pago='fondo').count()
        return becados * self.costo

    @property
    def deuda(self):
        deudores = self.asistencias.filter(pago='debe').count()
        return deudores * self.costo


class AsistenciaSimulacro(models.Model):
    OPCIONES_PAGO = [
        ('no_dio', 'No dió'),
        ('si', 'Pag'),
        ('fondo', 'Fondo'),
        ('debe', 'Debe'),
    ]

    simulacro = models.ForeignKey(Simulacro, on_delete=models.CASCADE, related_name='asistencias')
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE)
    pago = models.CharField(max_length=10, choices=OPCIONES_PAGO, default='no_dio')

    class Meta:
        unique_together = ('simulacro', 'matricula')
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"

    def __str__(self):
        return f"{self.matricula.alumno.nombres_completos} - {self.pago}"

    def save(self, *args, **kwargs):
        if self._state.adding and self.matricula.alumno.fondo_social:
            self.pago = 'fondo'
        super().save(*args, **kwargs)   

class FCMDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_devices')
    token = models.CharField(max_length=255, unique=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dispositivo de {self.user.username}"
    
class Venta(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=200)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

    @property
    def total_recaudado(self):
        return sum(
            v.total for v in self.ventas_alumnos.filter(pagado=True)
        )

class VentaAlumno(models.Model):

    venta = models.ForeignKey(Venta,related_name="ventas_alumnos",on_delete=models.CASCADE)
    alumno = models.ForeignKey(Alumno,related_name="compras",on_delete=models.CASCADE    )
    cantidad = models.PositiveIntegerField(default=1)
    pagado = models.BooleanField(default=False)
    entregado = models.BooleanField(default=False)
    observacion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('venta', 'alumno')

    @property
    def total(self):
        return self.cantidad * self.venta.precio_unitario

class Procedimiento(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    observacion = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

class Paso(models.Model):
    procedimiento = models.ForeignKey(Procedimiento, related_name='pasos', on_delete=models.CASCADE)
    orden = models.PositiveIntegerField()
    descripcion = models.TextField()
    archivo = models.FileField(upload_to="procesos/recursos/", blank=True, null=True)
    enlace_video = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.orden}. {self.descripcion}"