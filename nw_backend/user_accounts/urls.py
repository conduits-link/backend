from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('files/', views.EditorFileListView.as_view(), name='files'),
    path('file/<int:pk>', views.EditorFileDetailView.as_view(), name='file-detail'),
]
