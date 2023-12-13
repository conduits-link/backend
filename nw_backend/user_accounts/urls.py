from django.urls import path

from .views import send_registration_email, UserRegistrationAPIView, UserLoginAPIView, DocsCreateRetrieveView, DocRetrieveUpdateDestroyView

# Endpoints given in 
# https://github.com/dan-smith-tech/noteworthy/blob/main/docs/api.md

urlpatterns = [

    ############################
    # User authentication URLs #
    ############################

    path('auth/register', send_registration_email, name='register-email'),
    path('auth/register/<str:pk>', UserRegistrationAPIView.as_view(), name='register-account'),
    path('auth/login', UserLoginAPIView.as_view(), name='login'),

    ############################
    # Document controller URLs #
    ############################
    path('store/docs', DocsCreateRetrieveView.as_view(), name='create-view-docs'),
    path('store/docs/<int:pk>/', DocRetrieveUpdateDestroyView.as_view(), name='edit-doc'),
    
    #################
    # AI controller #
    #################   
    #path('generate/text', something, name='store-detail'), 

]