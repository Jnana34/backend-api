from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, UserLoginView, UserLogoutView, UserProfileView,
    OTPVerificationView, ForgotPasswordView, ResetPasswordView,
    UserAddressViewSet, UserPaymentMethodViewSet,CsrfTokenView,CurrentUserView
)

router = DefaultRouter()
router.register(r'addresses', UserAddressViewSet, basename='address')
router.register(r'payment-methods', UserPaymentMethodViewSet, basename='payment-method')

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
    
    # User management
    path('', include(router.urls)),
]
