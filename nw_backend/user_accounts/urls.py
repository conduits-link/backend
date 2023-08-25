from django.urls import path
from . import views
from django.conf.urls import include

urlpatterns = [
    path('', views.index, name='index'),
    path('files/', views.EditorFileListView.as_view(), name='files'),
    path('files/new/', views.new_file, name='new-file'),
    path('file/<int:pk>', views.EditorFileDetailView.as_view(), name='file-detail'),
    path('file/<int:pk>/edit', views.edit_file, name='edit-file'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', views.register, name='register'),
]
