from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, UserLoginView, UserLogoutView, UserProfileView,
    OTPVerificationView, ForgotPasswordView, ResetPasswordView,
    AddressListView,SetDefaultAddressView, UserPaymentMethodViewSet,CsrfTokenView,CurrentUserView
)
urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('csrf/', CsrfTokenView.as_view(), name='csrf'),
    path('user/', CurrentUserView.as_view(), name='user'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # OTP and Password Reset
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    #info
    path('addresses/', AddressListView.as_view(), name='user-addresses'),
    path('addresses/set-default/', SetDefaultAddressView.as_view(), name='set-default-address'),
    
    # User management
]
