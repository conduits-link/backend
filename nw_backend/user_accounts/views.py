from django.shortcuts import render
from django.views import generic

# Allows you to put @login_required before a view to hide it from logged-out users.
from django.contrib.auth.decorators import login_required

# Allows you to hide pages from logged-in users.
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

from .models import EditorFile

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_files = EditorFile.objects.all().count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1


    context = {
        'num_files': num_files,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)



class EditorFileListView(generic.ListView):
    model = EditorFile
    paginate_by = 10

class EditorFileDetailView(generic.DetailView):
    model = EditorFile

from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import UserCreationForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')  # Redirect to your home page
        else:
            # Form is invalid, render the template with errors
            return render(request, 'registration/register.html', {'form': form})
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
