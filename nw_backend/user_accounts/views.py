import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views import generic

from .models import EditorFile
from .forms import UserCreationForm, CreateEditorFile

class EditorFileListView(generic.ListView):
    model = EditorFile
    paginate_by = 10

class EditorFileDetailView(generic.DetailView):
    model = EditorFile

def index(request):
    """View function for home page of site."""

    # Count the number of text files.
    num_files = EditorFile.objects.all().count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # Display these variables on the homepage.
    context = {
        'num_files': num_files,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context=context)

def register(request):
    """New user account registration page."""
    
    # Process registration form if submitted.
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():

            # Save new user to database.
            user = form.save()

            # Log new user in.
            login(request, user)

            # Redirect to homepage after registration.
            return redirect('index')  
        
        # If form is invalid, render template with error details.
        return render(request, 'registration/register.html', {'form': form})

    # If no form is submitted, display empty form.
    return render(request, 'registration/register.html', {'form': UserCreationForm()})

@login_required
def new_file(request):

    # Process new file if submitted.
    if request.method == 'POST':
        form = CreateEditorFile(request.POST)

        if form.is_valid():
            # Create instance but don't save to DB yet.
            editor_file = form.save(commit=False)

            # Add necessary metadata.
            editor_file.date_created = datetime.datetime.today()
            editor_file.author = request.user.username

            # Save to DB.
            editor_file.save()

            # View the newly created file.
            return redirect('file-detail', pk=editor_file.pk)
        
        # If form is invalid, render template with error details.
        return render(request, 'user_accounts/newfile.html', {'form': form})
    
    # If no form is submitted, display empty form.
    return render(request, 'user_accounts/newfile.html', {'form': CreateEditorFile()})

@login_required
def edit_file(request, pk):

    # Retrieve the specified file.
    file_to_edit = get_object_or_404(EditorFile, pk=pk)

    # Process edits if submitted.
    if request.method == 'POST':

        # Populate form with the new text, and link it with the file we are editing.
        form = CreateEditorFile(request.POST, instance=file_to_edit)

        if form.is_valid():
            form.save()
            return redirect('file-detail', pk=pk)
    
    context = {
        'form': CreateEditorFile(instance=file_to_edit),
        'file_instance': file_to_edit,
    }

    # If no form is submitted, display edit form with specified file information.
    return render(request, 'user_accounts/editfile.html', context=context)

@login_required
def delete_file(pk):
    editor_file = get_object_or_404(EditorFile, pk=pk)   

    # We will eventually want to add a conditional here to check which user is trying to delete which file. 
    editor_file.delete()
    return redirect('files')