from django.shortcuts import render

def index(request):
    context = {}
    if(request.user.is_authenticated):
        context['user'] = request.user
    return render(request, 'index.html', context)
