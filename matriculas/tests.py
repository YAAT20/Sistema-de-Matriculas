from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse

from matriculas.context_processors import breadcrumb


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
