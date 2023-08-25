from django.shortcuts import render
from django.views import generic
import datetime
from .models import EditorFile
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserCreationForm, NewEditorFile

# Allows you to put @login_required before a view to hide it from logged-out users.
from django.contrib.auth.decorators import login_required

# Allows you to hide pages from logged-in users.
from django.contrib.auth.mixins import LoginRequiredMixin



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

import datetime

from django.shortcuts import render, get_object_or_404

@login_required
def new_file(request):
    if request.method == 'POST':
        form = NewEditorFile(request.POST)
        if form.is_valid():
            editor_file = form.save(commit=False)  # Create instance but don't save to DB yet
            editor_file.date_created = datetime.datetime.today()  # Set the current date and time
            editor_file.author = request.user.username
            editor_file.save()  # Save the instance with updated fields

            # Redirect to the detail page of the newly created file
            return redirect('file-detail', pk=editor_file.pk)
        else:
            # Form is invalid, render the template with errors
            return render(request, 'user_accounts/newfile.html', {'form': form})
    else:
        form = NewEditorFile()
    return render(request, 'user_accounts/newfile.html', {'form': form})

@login_required
def edit_file(request, pk):
    file_instance = get_object_or_404(EditorFile, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':
        form = NewEditorFile(request.POST, instance=file_instance)  # Pass the instance to update

        # Check if the form is valid:
        if form.is_valid():
            updated_file = form.save(commit=False)
            updated_file.date_created = datetime.datetime.today()
            updated_file.author = request.user.username
            updated_file.save()

            return redirect('file-detail', pk=pk)  # Redirect to file detail page

    # If this is a GET (or any other method) create the default form.
    else:
        form = NewEditorFile(instance=file_instance)  # Pass the instance to populate form

    context = {
        'form': form,
        'file_text': file_instance.file_text,
    }

    return render(request, 'user_accounts/newfile.html', {'form': form})
