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



class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        print("User registration initiated")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        print(f"User created: {user.email}")

        otp_token = self.generate_otp(user, 'registration')
        temp_token = str(uuid.uuid4())

        request.session[f'temp_registration_{temp_token}'] = {
            'user_id': str(user.id),
            'expires_at': (timezone.now() + timedelta(minutes=5)).isoformat()
        }
        print(f"Stored session token: temp_registration_{temp_token}")

        return Response({
            'message': 'User registered successfully. Please verify with OTP.',
            'requires_otp': True,
            'temp_token': temp_token
        }, status=status.HTTP_201_CREATED)

    def generate_otp(self, user, otp_type):
        print(f"Generating OTP for {user.email} of type {otp_type}")
        OTPToken.objects.filter(user=user, otp_type=otp_type, is_used=False).delete()
        otp = ''.join(random.choices(string.digits, k=6))

        otp_token = OTPToken.objects.create(
            user=user,
            token=otp,
            otp_type=otp_type,
            expires_at=timezone.now() + timedelta(minutes=5)
        )

        print(f"OTP for {user.email}: {otp}")

        send_mail(
        subject="Your OTP Verification Code",
        message=f"Your OTP is {otp}. It will expire in 10 minutes.",
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=[user.email],
        fail_silently=False,)
        return otp_token


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


class OTPVerificationView(generics.GenericAPIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        print("OTP verification request received")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        temp_token = serializer.validated_data['temp_token']
        otp = serializer.validated_data['otp']
        otp_type = serializer.validated_data['type']
        print(f"Verifying OTP: {otp} for type: {otp_type}")

        session_key = f'temp_registration_{temp_token}' if otp_type == 'registration' else f'temp_forgot_{temp_token}'
        session_data = request.session.get(session_key)

        if not session_data:
            print("Invalid or expired session token")
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=session_data['user_id'])
            print(f"User found: {user.email}")
        except User.DoesNotExist:
            print("User not found from session data")
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_token = OTPToken.objects.get(
                user=user,
                token=otp,
                otp_type=otp_type.replace('-', '_'),
                is_used=False
            )
        except OTPToken.DoesNotExist:
            print("Invalid OTP provided")
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if not otp_token.is_valid():
            print("OTP expired")
            return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

        otp_token.is_used = True
        otp_token.save()
        print("OTP verified and marked as used")

        if otp_type == 'registration':
            user.is_verified = True
            user.save()
            token, created = Token.objects.get_or_create(user=user)
            login(request, user)
            del request.session[session_key]
            print("User account verified and logged in")

            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Account verified successfully'
            })
        else:
            print("OTP verified for forgot password flow")
            return Response({'message': 'OTP verified successfully'})


class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        print("Forgot password request received")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

        otp_token = UserRegistrationView().generate_otp(user, 'forgot_password')
        temp_token = str(uuid.uuid4())
        request.session[f'temp_forgot_{temp_token}'] = {
            'user_id': str(user.id),
            'expires_at': (timezone.now() + timedelta(minutes=5)).isoformat()
        }
        print(f"Forgot password temp token created: {temp_token}")

        return Response({
            'message': 'OTP sent successfully',
            'requires_otp': True,
            'temp_token': temp_token
        })


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

class AddressListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = UserAddress.objects.filter(user=request.user)
        serializer = UserAddressSerializer(addresses, many=True)
        return Response(serializer.data)


class SetDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        address_id = request.data.get("address_id")
        if not address_id:
            return Response({"error": "Address ID is required"}, status=400)

        try:
            address = UserAddress.objects.get(id=address_id, user=request.user)
        except UserAddress.DoesNotExist:
            return Response({"error": "Address not found"}, status=404)

        UserAddress.objects.filter(user=request.user).update(is_default=False)
        address.is_default = True
        address.save()

        return Response({"message": "Default address updated", "address_id": str(address.id)}, status=200)

class CreateAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Create the address
        serializer = UserAddressSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()  # This will create a new address
            return Response({"message": "Address created successfully", "address": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        # Extracting the address_id from the request body
        address_id = request.data.get("address_id")

        if not address_id:
            return Response({"error": "Address ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the address by the ID and ensure it's owned by the authenticated user
            address = UserAddress.objects.get(id=address_id, user=request.user)
        except UserAddress.DoesNotExist:
            return Response({"error": "Address not found or does not belong to the user"}, status=status.HTTP_404_NOT_FOUND)

        # Delete the address
        address.delete()

        return Response({"message": "Address deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
class EditAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        # Print the incoming request data for debugging
        print(f"Request data: {request.data}")
        
        # Extract the address_id and address data from the request
        address_id = request.data.get("address_id")
        address_data = request.data.get("data")
        
        if not address_id:
            return Response({"error": "Address ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not address_data:
            return Response({"error": "Address data is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the address from the database
            address = UserAddress.objects.get(id=address_id, user=request.user)
        except UserAddress.DoesNotExist:
            return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        # Print the address that will be updated
        print(f"Address to be updated: {address}")

        # Pass the extracted address data to the serializer to update it
        # Since 'data' already contains the relevant information, we need to directly pass it
        serializer = UserAddressSerializer(address, data=address_data, partial=True, context={'request': request})

        if serializer.is_valid():
            # Print the data that will be saved
            print(f"Saving address with data: {serializer.validated_data}")
            
            # Save the updated address
            serializer.save()

            # Print confirmation of the successful save
            print(f"Address updated successfully: {serializer.data}")
            
            return Response({"message": "Address updated successfully", "address": serializer.data}, status=status.HTTP_200_OK)
        else:
            # Print the serializer errors if validation fails
            print(f"Serializer validation failed: {serializer.errors}")
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
