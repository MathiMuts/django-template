# example_app/views.py

from django.shortcuts import render
from django.views.decorators.cache import cache_page

@cache_page(10) # Cache page for 10s ( DO NOT USE FOR FORMS OR REACTIVE )
def index(request):
    import time
    print("Page served not from cache")
    return render(request, 'example_app/pages/index.html', {'time': time.time}) # -> Time will only update every 10s