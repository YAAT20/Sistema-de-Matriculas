from django.shortcuts import render


def app_selection_prelogin(request):
    return render(request, 'app_selection_prelogin.html')
