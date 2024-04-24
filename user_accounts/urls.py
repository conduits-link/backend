from django.urls import path
from .views import RegistrationEmailView, UserRegistrationView, UserLoginView, UserLogoutView, UserForgotView, UserResetPasswordView, DocsCreateRetrieveView, DocRetrieveUpdateDestroyView, PromptView, GenerateTextView, UserCreditsView, OrderFulfillmentWebhookView, CreditsSessionIDView

# Endpoints given in 
# https://github.com/dan-smith-tech/conduit/blob/main/docs/api.md

urlpatterns = [

    ############################
    # User authentication URLs #
    ############################

    path('auth/register', RegistrationEmailView.as_view(), name='register-email'),
    path('auth/register/<str:pk>', UserRegistrationView.as_view(), name='register-account'),
    path('auth/login', UserLoginView.as_view(), name='login'),
    path('auth/logout', UserLogoutView.as_view(), name='logout'),
    path('auth/forgot', UserForgotView.as_view(), name='forgot'),
    path('auth/forgot/<str:pk>', UserResetPasswordView.as_view(), name='reset'),

    ############################
    # Document controller URLs #
    ############################
    path('store/docs', DocsCreateRetrieveView.as_view(), name='create-view-docs'),
    path('store/docs/<str:pk>', DocRetrieveUpdateDestroyView.as_view(), name='edit-doc'),
    
    #################
    # AI controller #
    #################   
    path('prompts', PromptView.as_view(), name='prompts'), 
    path('generate/text', GenerateTextView.as_view(), name='generate-text'), 

    ############
    # Payments #
    ############

    path('credits', UserCreditsView.as_view(), name='credits'), 
    path('stripe-webhook', OrderFulfillmentWebhookView.as_view(), name='stripe-webhook'),
    path('credits/<str:pk>', CreditsSessionIDView.as_view(), name='credits-sessionid'), 

]