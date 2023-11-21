from django.urls import path

from .views import FileDetailView, FileCreateView, StoreView

urlpatterns = [
    path('files/<int:pk>/', FileDetailView.as_view(), name='file-detail'),
    path('files/upload/', FileCreateView.as_view(), name='file-upload'),
    path('store/', StoreView.as_view(), name='store-detail'),
]