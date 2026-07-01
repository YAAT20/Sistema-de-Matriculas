from marketing.models import RecursoMarketing

class RecursoMarketingService:

    @staticmethod
    def listar():

        return RecursoMarketing.objects.all()

    @staticmethod
    def total():

        return RecursoMarketing.objects.count()