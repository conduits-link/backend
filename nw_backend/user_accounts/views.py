from django.shortcuts import render

# Create your views here.

from .models import EditorFile

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_files = EditorFile.objects.all().count()

    context = {
        'num_files': num_files,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

from django.views import generic

class EditorFileListView(generic.ListView):
    model = EditorFile

class EditorFileDetailView(generic.DetailView):
    model = EditorFile
