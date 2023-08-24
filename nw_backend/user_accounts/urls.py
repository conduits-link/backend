from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('files/', views.EditorFileListView.as_view(), name='files'),
    path('file/<int:pk>', views.EditorFileDetailView.as_view(), name='file-detail'),
    path('register_account', views.register_account_request, name='register-account'),
    path('login', views.login_request, name='login'),
]
