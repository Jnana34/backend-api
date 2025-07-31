from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.middleware.csrf import get_token
from django.contrib.auth import login, logout
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
import random
import string
import uuid
from rest_framework.views import APIView
from .models import User, UserAddress, UserPaymentMethod, OTPToken
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserAddressSerializer, UserPaymentMethodSerializer,
    OTPVerificationSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

class CsrfTokenView(APIView):
    """GET /api/auth/csrf/"""
    permission_classes = [AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({'csrfToken': token})


class CurrentUserView(APIView):
    """GET /api/auth/user/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get(self, request):
        user = request.user
        return Response({
            'user': UserSerializer(user).data
        })



class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        print("User registration initiated")
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        if User.objects.filter(email=email).exists():
            return Response({'email': 'This email is already registered.'}, status=status.HTTP_400_BAD_REQUEST)

        temp_token = str(uuid.uuid4())
        self.generate_otp(request, temp_token, serializer.validated_data)

        return Response({
            'message': 'OTP sent to your email. Please verify to complete registration.',
            'temp_token': temp_token,
            'requires_otp': True
        }, status=status.HTTP_200_OK)

    def generate_otp(self, request, temp_token, user_data):
        otp = ''.join(random.choices(string.digits, k=6))

        # Store OTP and user data in session
        request.session[f'temp_registration_{temp_token}'] = {
            'data': user_data,
            'otp': otp,
            'expires_at': (timezone.now() + timedelta(minutes=5)).isoformat()
        }

        # Log and send OTP
        print(f"OTP for {user_data['email']}: {otp}")
        send_mail(
            subject="Your OTP Verification Code",
            message=f"Your OTP is {otp}. It will expire in 5 minutes.",
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[user_data['email']],
            fail_silently=False,
        )




class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print("Login request received")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        print(f"Login successful for user: {user.email}")

        token, created = Token.objects.get_or_create(user=user)

        login(request, user)
        user.last_login = timezone.now()
        user.save()

        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        })


class UserLogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(f"Logout request for user: {request.user.email}")
        try:
            request.user.auth_token.delete()
            print("Token deleted")
        except:
            print("No token to delete")

        logout(request)
        return Response({'message': 'Logout successful'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        print(f"Fetching profile for user: {self.request.user.email}")
        return self.request.user


class OTPVerificationView(APIView):
    def generate_unique_username(self,first_name, last_name):
        base = f"{first_name.lower()}{last_name.lower()}"
        while True:
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            username = f"{base}{suffix}"
            if not User.objects.filter(username=username).exists():
                return username
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        print("otp verification request received")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        temp_token = serializer.validated_data['temp_token']
        otp = serializer.validated_data['otp']
        otp_type = serializer.validated_data['type']
        print("otp:",otp,"type",otp_type)

        session_key = f'temp_registration_{temp_token}' if otp_type == 'registration' else f'temp_forgot_{temp_token}'
        session_data = request.session.get(session_key)

        if not session_data:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        if session_data['otp'] != otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_type == 'registration':
            user_data = session_data['data']
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            username = self.generate_unique_username(first_name, last_name)
            print("Creating user with:", user_data)
            user = User.objects.create_user(
            username=username,
            email=user_data['email'],
            password=user_data['password']
            )
            user.is_verified = True
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
            login(request, user)
            del request.session[session_key]

            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Account verified and created successfully'
            })

        elif otp_type == 'forgot-password':
            # Implement forgot password OTP verification logic
            # Only delete OTP session here; reset happens in ResetPasswordView
            return Response({'message': 'OTP verified successfully'})



class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        print("Forgot password request received")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data['email_or_phone']
        print(f"Identifier received: {identifier}")

        user = None
        if '@' in identifier:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(phone=identifier)
            except User.DoesNotExist:
                pass

        if not user:
            print("User not found for forgot password")
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

        temp_token = str(uuid.uuid4())
        otp = ''.join(random.choices(string.digits, k=6))

        # ✅ Store OTP and user ID in session
        request.session[f'temp_forgot_{temp_token}'] = {
            'otp': otp,
            'user_id': str(user.id),
            'expires_at': (timezone.now() + timedelta(minutes=5)).isoformat()
        }

        print(f"Forgot password OTP for {user.email}: {otp}")
        send_mail(
            subject="Your OTP for Password Reset",
            message=f"Your OTP is {otp}. It will expire in 5 minutes.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

        print(f"Forgot password temp token created: {temp_token}")
        return Response({
            'message': 'OTP sent successfully',
            'temp_token': temp_token,
            'requires_otp': True
        }, status=status.HTTP_200_OK)
        


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        print("Reset password request received")
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)

        temp_token = serializer.validated_data['temp_token']
        new_password = serializer.validated_data['new_password']
        session_key = f'temp_forgot_{temp_token}'

        session_data = request.session.get(session_key)
        if not session_data:
            print("Invalid or expired token for reset password")
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=session_data['user_id'])
            print(f"User found for reset password: {user.email}")
        except User.DoesNotExist:
            print("User not found for reset password")
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        del request.session[session_key]
        print("Password reset successfully")

        return Response({'message': 'Password reset successfully'})


class UserAddressViewSet(viewsets.ModelViewSet):
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print(f"Fetching addresses for user: {self.request.user.email}")
        return UserAddress.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        print(f"Setting default address: {pk} for user: {request.user.email}")
        address = self.get_object()
        UserAddress.objects.filter(user=request.user).update(is_default=False)
        address.is_default = True
        address.save()
        return Response({'message': 'Default address updated'})


class UserPaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = UserPaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print(f"Fetching payment methods for user: {self.request.user.email}")
        return UserPaymentMethod.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        print(f"Setting default payment method: {pk} for user: {request.user.email}")
        payment_method = self.get_object()
        UserPaymentMethod.objects.filter(user=request.user).update(is_default=False)
        payment_method.is_default = True
        payment_method.save()
        return Response({'message': 'Default payment method updated'})
