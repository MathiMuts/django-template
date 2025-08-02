# example_app/views.py

from django.shortcuts import render

def index(request):
    return render(request, 'example_app/pages/index.html')