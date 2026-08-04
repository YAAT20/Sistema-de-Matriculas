from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from matriculas.context_processors import breadcrumb
from matriculas.models import (
    Alumno,
    Apoderado,
    Ciclo,
    Horario,
    Matricula,
    Procedimiento,
    Seguimiento,
    Turno,
)


class BreadcrumbContextProcessorTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_breadcrumb_for_alumno_list(self):
        request = self.factory.get(reverse('matriculas:alumno_list'))
        request.resolver_match = resolve(reverse('matriculas:alumno_list'))

        context = breadcrumb(request)

        self.assertIn('breadcrumb', context)
        self.assertEqual(context['breadcrumb'][0]['titulo'], 'Inicio')
        self.assertEqual(context['breadcrumb'][-1]['titulo'], 'Alumnos')

    def test_breadcrumb_for_matricula_detail(self):
        request = self.factory.get('/matriculas/1/')
        request.resolver_match = resolve('/matriculas/1/')

        context = breadcrumb(request)

        self.assertIn('breadcrumb', context)
        self.assertEqual(context['breadcrumb'][0]['titulo'], 'Inicio')
        self.assertEqual(context['breadcrumb'][-1]['titulo'], 'Detalle')


class MatriculaListViewFilterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(self.user)

        self.ciclo = Ciclo.objects.create(
            nombre='Ciclo Test',
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date(),
            activo=True,
        )
        self.turno = Turno.objects.create(nombre='Mañana')
        self.horario = Horario.objects.create(
            nombre='Horario Test',
            hora_inicio1='08:00:00',
            hora_fin1='10:00:00',
            dias_bloque1='L,M',
        )

    def _create_matricula(self, estado, codigo):
        alumno = Alumno.objects.create(
            grado_estudios='1s',
            nombres_completos=f'Alumno {codigo}',
            dni=f'100000{codigo}',
            sexo='M',
            celular_llamadas='987654321',
            numero_whatsapp='987654321',
            fecha_nacimiento='2010-01-01',
        )
        apoderado = Apoderado.objects.create(
            nombre_completo=f'Apoderado {codigo}',
            dni=f'200000{codigo}',
            celular='912345678',
            parentesco='Padre',
            abreviatura='Sr.',
        )
        apoderado.alumnos.add(alumno)

        return Matricula.objects.create(
            alumno=alumno,
            apoderado=apoderado,
            monto=100.00,
            cuotas=1,
            modalidad='presencial',
            ciclo=self.ciclo,
            turno=self.turno,
            horario=self.horario,
            usuario_registro=self.user,
            tipo_matricula='regular',
            estado=estado,
        )

    def test_filter_by_estado_param(self):
        self._create_matricula('activa', '1')
        self._create_matricula('congelada', '2')
        self._create_matricula('finalizada', '3')

        response = self.client.get(reverse('matriculas:matricula_list'), {'estado': 'congelada'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Congelada')
        self.assertEqual(len(response.context['matriculas']), 1)
        self.assertEqual(response.context['matriculas'][0].estado, 'congelada')


class UserDeletionPreservesRecordsTests(TestCase):
    def test_user_deletion_keeps_registered_records(self):
        User = get_user_model()
        user = User.objects.create_user(username='tester', password='secret123')

        ciclo = Ciclo.objects.create(
            nombre='Ciclo Test',
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date(),
            activo=True,
        )
        turno = Turno.objects.create(nombre='Mañana')
        horario = Horario.objects.create(
            nombre='Horario Test',
            hora_inicio1='08:00:00',
            hora_fin1='10:00:00',
            dias_bloque1='L,M',
        )
        alumno = Alumno.objects.create(
            grado_estudios='1s',
            nombres_completos='Ana Pérez',
            dni='12345678',
            sexo='F',
            celular_llamadas='987654321',
            numero_whatsapp='987654321',
            fecha_nacimiento='2010-01-01',
        )
        apoderado = Apoderado.objects.create(
            nombre_completo='Juan Pérez',
            dni='87654321',
            celular='912345678',
            parentesco='Padre',
            abreviatura='Señor',
        )
        apoderado.alumnos.add(alumno)

        matricula = Matricula.objects.create(
            alumno=alumno,
            apoderado=apoderado,
            monto=100.00,
            cuotas=1,
            modalidad='presencial',
            ciclo=ciclo,
            turno=turno,
            horario=horario,
            usuario_registro=user,
            tipo_matricula='regular',
        )
        seguimiento = Seguimiento.objects.create(
            matricula=matricula,
            usuario=user,
            texto='Registro creado',
        )
        procedimiento = Procedimiento.objects.create(
            titulo='Proceso de prueba',
            creado_por=user,
        )

        user.delete()

        matricula.refresh_from_db()
        seguimiento.refresh_from_db()
        procedimiento.refresh_from_db()

        self.assertTrue(Matricula.objects.filter(pk=matricula.pk).exists())
        self.assertIsNone(matricula.usuario_registro_id)
        self.assertTrue(Seguimiento.objects.filter(pk=seguimiento.pk).exists())
        self.assertIsNone(seguimiento.usuario_id)
        self.assertTrue(Procedimiento.objects.filter(pk=procedimiento.pk).exists())
        self.assertIsNone(procedimiento.creado_por_id)
