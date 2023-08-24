from django.shortcuts import render

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

from django.views import generic

class EditorFileListView(generic.ListView):
    model = EditorFile
    paginate_by = 10

class EditorFileDetailView(generic.DetailView):
    model = EditorFile

from django.shortcuts import  redirect
from .forms import NewUserForm
from django.contrib.auth import login
from django.contrib import messages

def register_account_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful." )
			return redirect("index")
		messages.error(request, "Unsuccessful registration. Invalid information.")
	form = NewUserForm()
	return render (request=request, template_name="register_account.html", context={"register_account_form":form})

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm #add this

def login_request(request):
	if request.method == "POST":
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				messages.info(request, f"You are now logged in as {username}.")
				return redirect("index")
			else:
				messages.error(request,"Invalid username or password.")
		else:
			messages.error(request,"Invalid username or password.")
	form = AuthenticationForm()
	return render(request=request, template_name="login.html", context={"login_form":form})