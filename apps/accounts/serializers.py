from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserAddress, UserPaymentMethod, OTPToken
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password', 'confirm_password']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_phone(self, value):
        if value and not re.match(r'^\+?[\d\s\-\(\)]{10,}$', value.replace(' ', '')):
            raise serializers.ValidationError("Please enter a valid phone number.")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            username=validated_data['email'],  # Use email as username
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()  # Can be email or phone
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        identifier = attrs.get('identifier')
        password = attrs.get('password')
        
        if identifier and password:
            # Try to find user by email or phone
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
            
            if user and user.check_password(password):
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Invalid credentials.')
        else:
            raise serializers.ValidationError('Must include identifier and password.')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'avatar', 
                 'is_verified', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'title', 'full_name', 'phone', 'street_address', 
                 'city', 'state', 'postal_code', 'country', 'is_default']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # If this is set as default, unset other defaults
        if validated_data.get('is_default'):
            UserAddress.objects.filter(user=validated_data['user']).update(is_default=False)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # If this is set as default, unset other defaults
        if validated_data.get('is_default'):
            UserAddress.objects.filter(user=instance.user).exclude(id=instance.id).update(is_default=False)
        
        return super().update(instance, validated_data)

class UserPaymentMethodSerializer(serializers.ModelSerializer):
    card_number_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPaymentMethod
        fields = ['id', 'type', 'card_number', 'card_number_masked', 'card_holder_name', 
                 'expiry_month', 'expiry_year', 'paypal_email', 'is_default']
        read_only_fields = ['id', 'card_number_masked']
        extra_kwargs = {
            'card_number': {'write_only': True}
        }
    
    def get_card_number_masked(self, obj):
        if obj.card_number:
            return f"**** **** **** {obj.card_number[-4:]}"
        return None
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # If this is set as default, unset other defaults
        if validated_data.get('is_default'):
            UserPaymentMethod.objects.filter(user=validated_data['user']).update(is_default=False)
        
        return super().create(validated_data)

class OTPVerificationSerializer(serializers.Serializer):
    temp_token = serializers.CharField()
    otp = serializers.CharField(max_length=6, min_length=6)
    type = serializers.ChoiceField(choices=['registration', 'forgot-password'])

class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()

class ResetPasswordSerializer(serializers.Serializer):
    temp_token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'title', 'full_name', 'phone', 'street_address', 
                 'city', 'state', 'postal_code', 'country', 'is_default']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # If this is set as default, unset other defaults
        if validated_data.get('is_default'):
            UserAddress.objects.filter(user=validated_data['user']).update(is_default=False)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # If this is set as default, unset other defaults
        if validated_data.get('is_default'):
            UserAddress.objects.filter(user=instance.user).exclude(id=instance.id).update(is_default=False)
        
        return super().update(instance, validated_data)

class UserPaymentMethodSerializer(serializers.ModelSerializer):
    card_number_masked = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPaymentMethod
        fields = ['id', 'type', 'card_number', 'card_number_masked', 'card_holder_name', 
                 'expiry_month', 'expiry_year', 'paypal_email', 'is_default']
        read_only_fields = ['id', 'card_number_masked']
        extra_kwargs = {
            'card_number': {'write_only': True}
        }
    
    def get_card_number_masked(self, obj):
        if obj.card_number:
            return f"**** **** **** {obj.card_number[-4:]}"
        return None
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # If this is set as default, unset other defaults
        if validated_data.get('is_default'):
            UserPaymentMethod.objects.filter(user=validated_data['user']).update(is_default=False)
        
        return super().create(validated_data)

class OTPVerificationSerializer(serializers.Serializer):
    temp_token = serializers.CharField()
    otp = serializers.CharField(max_length=6, min_length=6)
    type = serializers.ChoiceField(choices=['registration', 'forgot-password'])

class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()

class ResetPasswordSerializer(serializers.Serializer):
    temp_token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
