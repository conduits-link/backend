from django.urls import path
from .views import RegistrationEmailAPIView, UserRegistrationAPIView, UserLoginAPIView, DocsCreateRetrieveView, DocRetrieveUpdateDestroyView, generate_text
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Endpoints given in 
# https://github.com/dan-smith-tech/conduit/blob/main/docs/api.md

urlpatterns = [

    # SimpleJWT URLs.
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    ############################
    # User authentication URLs #
    ############################

    path('auth/register', RegistrationEmailAPIView.as_view(), name='register-email'),
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
    path('generate/text', generate_text, name='generate-text'), 

]