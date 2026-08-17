from django.db.models import Avg, Count
from datetime import datetime, timedelta
from .models import CustomUser, ContactMessage, HelpUsImprove, PhoneVerification
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers
User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    phone_number = serializers.CharField(max_length=15)
    role = serializers.ChoiceField(
        choices=['customer', 'merchant', 'rider'], default='customer')

    class Meta:
        model = CustomUser
        fields = [
            "full_name",
            "email",
            "password",
            "role",
            "phone_number",
        ]

    def validate_email(self, value):
        if value:
            value = value.strip().lower()
            if CustomUser.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already exists.")
        return value or None

    def validate_phone_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        password = validated_data.pop("password")
        role = validated_data.pop("role", "customer")
        validated_data.pop("username", None)  # Remove username if present

        # Split full name into first/last
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Generate unique username
        base_username = (first_name + last_name).lower()
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user
        user = CustomUser.objects.create(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            username=username,
            **validated_data
        )
        user.set_password(password)
        user.role = role
        user.is_active = True

        phone_number = user.phone_number
        if phone_number and PhoneVerification.objects.filter(
                phone_number=phone_number, is_verified=True).exists():
            user.is_phone_verified = True

        user.save()

        # Create role-specific profile
        from apps.customer.models import CustomerProfile
        from apps.merchant.models import MerchantProfile
        from apps.rider.models import RiderProfile

        if role == 'merchant':
            MerchantProfile.objects.get_or_create(user=user)
        elif role == 'rider':
            RiderProfile.objects.get_or_create(user=user)
        else:
            CustomerProfile.objects.get_or_create(user=user)

        return user
    
    
class CustomUserAllSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'is_active', 'full_name',
                  'email', 'role', 'address', 'phone_number', 'photo',]
        

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'full_name', 'email', 'is_active',
                  'role', 'address', 'phone_number', 'photo', 'created_at')
        read_only_fields = ('id', 'username', 'is_active',)

    def validate_email(self, value):
        if value:
            value = value.strip().lower()
            existing = CustomUser.objects.filter(email=value)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError("Email already exists.")
        return value or None

    def validate_phone_number(self, value):
        if value:
            value = value.strip()
            existing = CustomUser.objects.filter(phone_number=value)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError("This phone number is already registered.")
        return value or None

    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)        
    


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = str(data['identifier']).strip()
        password = data['password']

        # Find user by phone number, email or username
        user = (
            User.objects.filter(phone_number=identifier).first()
            or User.objects.filter(email__iexact=identifier).first()
            or User.objects.filter(username=identifier).first()
        )

        # If the user is not found, raise an error for identifier
        if not user:
            raise serializers.ValidationError(
                {"identifier": "Invalid credentials. Please check your phone number, email or username."})

        # Check if the user is active
        if not user.is_active:
            raise serializers.ValidationError(
                {"identifier": "Your account is not active. Please verify your phone number or email."})

        # Check password manually and raise an error for password
        if not user.check_password(password):
            raise serializers.ValidationError(
                {"password": "Incorrect password. Please try again."})

        # Authenticate the user with the provided password if the account is active and verified
        user = authenticate(username=user.username, password=password)

        if not user:
            raise serializers.ValidationError(
                "Invalid credentials. Please check your phone number, email or password.")

        return {"user": user}


class SendPhoneOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value


class VerifyPhoneOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

    def validate_phone_number(self, value):
        return value.strip()

    def validate(self, data):
        try:
            verification = PhoneVerification.objects.get(
                phone_number=data['phone_number'])
        except PhoneVerification.DoesNotExist:
            raise serializers.ValidationError(
                {"phone_number": "No OTP has been sent to this phone number. Please request a new OTP."})

        if verification.is_otp_expired():
            raise serializers.ValidationError(
                {"otp": "OTP expired. Please request a new one."})

        if verification.attempts >= 5:
            raise serializers.ValidationError(
                {"otp": "Too many failed attempts. Please request a new OTP."})

        if verification.otp != data['otp']:
            verification.attempts += 1
            verification.save(update_fields=['attempts'])
            raise serializers.ValidationError(
                {"otp": "Invalid OTP."})

        verification.is_verified = True
        verification.save(update_fields=['is_verified'])
        return data


class TokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=15)

    def validate(self, data):
        email = (data.get('email') or '').strip()
        phone_number = (data.get('phone_number') or '').strip()
        if not email and not phone_number:
            raise serializers.ValidationError(
                {"identifier": "Either email or phone_number is required."})
        if email and phone_number:
            raise serializers.ValidationError(
                {"identifier": "Provide only one of email or phone_number."})
        if email and not User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."})
        if phone_number and not User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError(
                {"phone_number": "User with this phone number does not exist."})
        return data


class VerifyResetOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")

        try:
            verification = PhoneVerification.objects.get(
                phone_number=data['phone_number'])
        except PhoneVerification.DoesNotExist:
            raise serializers.ValidationError(
                {"otp": "No OTP has been sent to this phone number. Please request a new one."})

        if verification.is_otp_expired():
            raise serializers.ValidationError(
                {"otp": "OTP expired. Please request a new one."})

        if verification.attempts >= 5:
            raise serializers.ValidationError(
                {"otp": "Too many failed attempts. Please request a new OTP."})

        if verification.otp != data['otp']:
            verification.attempts += 1
            verification.save(update_fields=['attempts'])
            raise serializers.ValidationError({"otp": "Invalid OTP."})

        return data


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                "New password and confirmation password do not match.")
        return data


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["id", "full_name", "email", "subject", "message", "created_at"]
        read_only_fields = ["id", "created_at"]
 
        
class HelpUsImproveSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = HelpUsImprove
        fields = ["id", "user", "improve_message"]
        read_only_fields = ["user"]        
        


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "username", "password", "full_name",
            "role", "is_active", "address", "phone_number", "photo"
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user        