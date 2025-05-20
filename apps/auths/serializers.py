from django.db.models import Avg, Count
from datetime import datetime, timedelta
from .models import CustomUser, ContactMessage, HelpUsImprove
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers
User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6)
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

    def validate(self, data):
        # Check if email already exists
        if CustomUser.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError({"email": "Email already exists."})

        return data

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

    class Meta:
        model = CustomUser
        fields = ('id', 'full_name', 'email', 'is_active',
                  'role', 'address', 'phone_number', 'photo', 'created_at')
        read_only_fields = ('id', 'username', 'email', 'is_active',)

    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)        
    


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data['identifier']
        password = data['password']

        # Find user either by username or email
        user = None
        if '@' in identifier and '.' in identifier:
            user = User.objects.filter(email=identifier).first()
        else:
            user = User.objects.filter(username=identifier).first()

        # If the user is not found, raise an error for identifier
        if not user:
            raise serializers.ValidationError(
                {"identifier": "Invalid credentials. Please check your email or username."})

        # Check if the user is active
        if not user.is_active:
            raise serializers.ValidationError(
                {"identifier": "Your account is not active. Please verify your email."})

        # Check password manually and raise an error for password
        if not user.check_password(password):
            raise serializers.ValidationError(
                {"password": "Incorrect password. Please try again."})

        # Authenticate the user with the provided password if the account is active and verified
        user = authenticate(username=user.username, password=password)

        if not user:
            raise serializers.ValidationError(
                "Invalid credentials. Please check your email or password.")

        return {"user": user}


class TokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email does not exist.")
        return value


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