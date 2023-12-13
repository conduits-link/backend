from django.urls import path

from .views import DocsCreateRetrieveView, DocRetrieveUpdateDestroyView

# Endpoints given in 
# https://github.com/dan-smith-tech/noteworthy/blob/main/docs/api.md

urlpatterns = [

    ############################
    # User authentication URLs #
    ############################

    path('auth/register', something, name='register-email'),
    path('auth/register/<int:pk>', something, name='register-account'),
    path('auth/login', something, name='login'),

    ############################
    # Document controller URLs #
    ############################
    path('store/docs', DocsCreateRetrieveView.as_view(), name='create-view-docs'),
    path('store/docs/<int:pk>/', DocRetrieveUpdateDestroyView.as_view(), name='edit-doc'),
    
    #################
    # AI controller #
    #################   
    path('generate/text', something, name='store-detail'), 

]