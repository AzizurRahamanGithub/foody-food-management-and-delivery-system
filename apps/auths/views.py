from ..core.response import failure_response, success_response
from rest_framework import viewsets, permissions, status
from ..core.pagination import CustomPagination
from .models import CustomUser
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.db.models import Q
import os
from rest_framework.pagination import PageNumberPagination
import random
from django.utils import timezone
from django.contrib.auth import login, get_user_model, update_session_auth_hash
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import  urlsafe_base64_encode
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserProfile, HelpUsImprove, CustomUser
from rest_framework import viewsets, permissions
from .serializers import (
    UserRegisterSerializer, LoginSerializer, UserSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, PasswordChangeSerializer, CustomUserAllSerializer, ContactMessageSerializer, HelpUsImproveSerializer, AdminUserSerializer
)
from .tokens import email_activation_token
from rest_framework.authentication import TokenAuthentication
from apps.core.response import failure_response, success_response
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from ..core.crud import DynamicModelViewSet

from apps.notification.utils import notify_admins


BASE_URL = os.getenv('BASE_URL')
User = get_user_model()



class RegisterAPIView(APIView):
    permission_classes= [AllowAny]
    authentication_classes= []
    
    def post(self, request):
        
        try:
            serializer = UserRegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            # Notify admins only
            notify_admins(
                title="New User Registered",
                message=f"{user.full_name or user.username} just signed up."
            )
            
            return success_response("User Registered successfully", data= serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return failure_response("Validation Error", error=e.detail)
        
        except Exception as e:
            return failure_response("An error occurred", error= str(e), status= status.HTTP_500_INTERNAL_SERVER_ERROR)


class DetailSingleProfile(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response("User details retrieved successfully", serializer.data)


class ProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response("User details retrieved successfully", serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data
        # Proceed with the regular update logic
        serializer = self.get_serializer(
            instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return success_response("Profile updated successfully", serializer.data)


class UserAPIView(APIView):
    """
    GET → List all users
    POST → Create new user
    """

    def get(self, request):
        try:
            users = CustomUser.objects.all()
            serializer = UserSerializer(users, many=True)
            return success_response("Users retrieved successfully", serializer.data)
        except Exception as e:
            return failure_response("Failed to retrieve users", str(e))

    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return success_response("User created successfully", serializer.data, status=status.HTTP_201_CREATED)
            return failure_response("User creation failed", serializer.errors)
        except Exception as e:
            return failure_response("An error occurred while creating user", str(e))


class UserDetailAPIView(APIView):
  
    permission_classes=[IsAuthenticated]

    def get_object(self, pk):
        try:
            return CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return None

    def get(self, request, pk):
            user = self.get_object(pk)
            if user:
                serializer = UserSerializer(user)
                return success_response("User retrieved successfully", serializer.data)
            return failure_response("User not found", status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            user = self.get_object(pk)
            if user:
                serializer = UserSerializer(user, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return success_response("User updated successfully", serializer.data)
                return failure_response("Update failed", serializer.errors)
            return failure_response("User not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return failure_response("An error occurred while updating user", str(e))

    def delete(self, request, pk):
        try:
            user = self.get_object(pk)
            if user:
                user.delete()
                return success_response("User deleted successfully", data={})
            return failure_response("User not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return failure_response("An error occurred while deleting user", str(e))


class VerifyOTPAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            user = CustomUser.objects.get(email=email)
            profile = user.userprofile
        except CustomUser.DoesNotExist:
            return failure_response("Invalid email.", {})

        # Check OTP
        if profile.is_otp_expired():
            return failure_response("OTP expired. Please request a new one.", {})

        if profile.otp != otp:
            return failure_response("Invalid OTP.", {})

        # Mark user as verified
        user.is_active = True
        user.is_verified = True
        user.save()

        profile.otp = None  # clear otp
        profile.save()

        return success_response("Account verified successfully.", {"email": user.email})


class ResendOTPAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")

        try:
            user = CustomUser.objects.get(email=email)
            profile = user.userprofile
        except CustomUser.DoesNotExist:
            return failure_response("Invalid email.", {})

        otp = str(random.randint(100000, 999999))
        profile.otp = otp
        profile.otp_created_at = timezone.now()
        profile.save()
        
        #send email 
        email_subject = "Your OTP for Verification"
        email_body = render_to_string(
            "reset_password_email.html",
            {
                "otp": otp,
                "subject": "Email Verification",
                "message": "Use the following OTP to verify your account.",
            },
        )
        email = EmailMultiAlternatives(email_subject, "", to=[user.email])
        email.attach_alternative(email_body, "text/html")
        email.send()

        # ✅ return the string email, not the object
        return success_response("A new OTP has been sent to your email.", {"email": user.email})


class ResendVerificationEmailAPIView(APIView):
    """
    This view allows users to request a resend of the verification email if they
    haven't received it or missed it.
    """

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, email=email)

        if user.is_verified:
            return Response(
                {'message': 'User is already verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_active:
            return Response(
                {'message': 'User is already active.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate token and uid for verification link
        token = email_activation_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        confirm_link = f"{BASE_URL}/api/v1/auth/active/{uid}/{token}/"
        email_subject = "Confirm Your Email"
        email_body = render_to_string(
            'confirm_email.html', {'confirm_link': confirm_link})

        email = EmailMultiAlternatives(email_subject, '', to=[user.email])
        email.attach_alternative(email_body, "text/html")

        email.send()

        return Response(
            {'success': True, 'message': 'Verification email has been resent. Please check your email.'},
            status=status.HTTP_200_OK
        )


class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user(self, user):
        refresh_token = super().for_user(user)

        # Add custom claims
        refresh_token.payload['username'] = user.username
        refresh_token.payload['email'] = user.email
        refresh_token.payload['role'] = user.role

        return refresh_token


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            refresh = CustomRefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response({
                'success': True,
                'statusCode': status.HTTP_200_OK,
                'message': 'Login successful',
                'data': {
                    "user_id": user.id,
                    'username': user.username,
                    'role': user.role,
                    'access': access_token,
                    'refresh': refresh_token,
                }
            })

            response.set_cookie('refresh_token', refresh_token,
                                httponly=True, secure=True)

            login(request, user)
            return response

        first_error_message = next(iter(serializer.errors.values()))[0]
        return Response({
            'success': False,
            'statusCode': status.HTTP_400_BAD_REQUEST,
            'message': first_error_message,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            message="You have access!",
            data={},
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

                response = success_response("Logout successful")
                # Delete the refresh token cookie
                response.delete_cookie('refresh_token')
                return response
            return failure_response("Refresh token not provided")
        except Exception as e:
            return failure_response("Logout failed", str(e), status.HTTP_400_BAD_REQUEST)


class GetNewAccessTokenView(APIView):
    """Get new access token section."""
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate and create a new access token
            new_access = RefreshToken(refresh_token).access_token
            return Response(
                {"access": str(new_access)},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # Check if the old password is correct
        if not user.check_password(old_password):
            return failure_response("Incorrect old password", {"detail": "Incorrect old password"}, status.HTTP_400_BAD_REQUEST)

        # Update password
        user.set_password(new_password)
        user.save()

        # Update session to prevent logout after password change
        update_session_auth_hash(request, user)

        return success_response({"message": "Password changed successfully"}, status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    Send password reset link to user's email
    """

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]  
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return failure_response(
                "User with this email does not exist.",
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build password reset URL
        reset_url = f"{request.scheme}://{request.get_host()}/api/v1/auth/reset-password/{uid}/{token}/"
         
        # Send email
        subject = "Password Reset Request"
        body = render_to_string(
            "reset_password_email.html",
            {"reset_url": reset_url, "user": user},
        )
        email_message = EmailMultiAlternatives(subject, "", to=[user.email])
        email_message.attach_alternative(body, "text/html")
        email_message.send()

        return success_response(
            "Password reset link sent to your email.",
            {"email": user.email,
             "reset_url": reset_url
             },
            status=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):
    def post(self, request, uidb64, token):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return failure_response("Invalid link.", status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return failure_response("Token is invalid or expired.", status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['password'])
        user.save()
        return success_response("Password has been reset successfully.")


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AllUsers(viewsets.ModelViewSet):
    queryset = User.objects.filter().order_by('-id')
    serializer_class = CustomUserAllSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CustomPagination

    # GET - Retrieve List of Active Users
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return success_response("User list retrieved successfully", serializer.data)
        except Exception as e:
            return failure_response("Failed to retrieve user list", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # POST - Create a New User
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return success_response("User created successfully", serializer.data, status.HTTP_201_CREATED)
            return failure_response("User creation failed", serializer.errors)
        except Exception as e:
            return failure_response("An error occurred while creating the user", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # GET - Retrieve a Single User
    def retrieve(self, request, pk=None):
        try:
            user = get_object_or_404(User, pk=pk)
            serializer = self.get_serializer(user)
            return success_response("User details retrieved successfully", serializer.data)
        except Exception as e:
            return failure_response("Failed to retrieve user details", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PUT - Update a User
    def update(self, request, pk=None):
        try:
            user = get_object_or_404(User, pk=pk)
            serializer = self.get_serializer(
                user, data=request.data, partial=False)
            if serializer.is_valid():
                serializer.save()
                return success_response("User updated successfully", serializer.data)
            return failure_response("User update failed", serializer.errors)
        except Exception as e:
            return failure_response("An error occurred while updating the user", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # PATCH - Partially Update a User
    def partial_update(self, request, pk=None):
        try:
            user = get_object_or_404(User, pk=pk)
            serializer = self.get_serializer(
                user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return success_response("User partially updated successfully", serializer.data)
            return failure_response("User partial update failed", serializer.errors)
        except Exception as e:
            return failure_response("An error occurred while partially updating the user", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # DELETE - Deactivate a User (Soft Delete)
    def destroy(self, request, pk=None):
        try:
            user = get_object_or_404(User, pk=pk)
            user.is_active = False  # Soft delete instead of hard delete
            user.save()
            return success_response("User deactivated successfully", None, status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return failure_response("Failed to deactivate user", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleOauth(APIView):

    def post(self, request):
        email = request.data.get("email")
        name = request.data.get("name")

        if not email or not name:
            return Response({"error": "Email and name is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the email exists
        user = User.objects.filter(Q(email=email) | Q(username=email)).first()

        if user:
            # If the user exists, generate JWT tokens with custom claims
            refresh = CustomRefreshToken.for_user(
                user)  # Using the custom token class
            refresh_token = str(refresh)
            access_token = str(refresh.access_token)

            return Response({
                "success": True,
                "statusCode": status.HTTP_200_OK,
                "message": "Login successful",
                "data": {
                    "access": access_token,
                    "refresh": refresh_token,
                }
            })
        else:
            # If the user does not exist, create a new user
            username = email.split(
                "@")[0] if "@" in email else f"user_{os.urandom(4).hex()}"
            first_name = name.split(" ")[0]
            last_name = " ".join(name.split(" ")[1:])

            # Ensure the username is unique, and if not, append a random 4-digit number
            while User.objects.filter(username=username).exists():
                username = f"{username}{random.randint(1000, 9999)}"

            user = User.objects.create_user(
                username=username, email=email, first_name=first_name, last_name=last_name, password=os.urandom(24).hex())

            # Make sure to set the 'is_active' field to True
            user.is_active = True
            user.role = 'user'

            try:
                # Save the user with transaction to ensure consistency
                with transaction.atomic():
                    user.save()

                # Debugging: Print the user status after saving
                print(
                    f"User {user.username} is_active set to {user.is_active}")

            except Exception as e:
                # Catch any potential error during save
                return Response({"error": f"Error saving user: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Generate JWT tokens for the new user with custom claims
            refresh = CustomRefreshToken.for_user(
                user)
            refresh_token = str(refresh)
            access_token = str(refresh.access_token)

            return Response({
                "success": True,
                "statusCode": status.HTTP_200_OK,
                "message": "User created and logged in successfully",
                "data": {
                    "user": {
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role,
                    },
                    "access": access_token,
                    "refresh": refresh_token,
                }
            })


from django.conf import settings

class ContactMessageView(APIView):
    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)

        if serializer.is_valid():
            contact_message = serializer.save()

            subject = f"New Contact Message: {contact_message.subject}"
            message = (
                f"Name: {contact_message.full_name}\n"
                f"Email: {contact_message.email}\n\n"
                f"Message:\n{contact_message.message}"
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,   # from (Brevo verified sender)
                [settings.CONTACT_EMAIL],      # to   (where you receive)
                fail_silently=False,
            )

            return success_response(
                {"message": "Your message has been sent successfully."},
                status=status.HTTP_201_CREATED
            )

        return failure_response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class HelpUsImproveView(DynamicModelViewSet):
    queryset = HelpUsImprove.objects.all()
    serializer_class = HelpUsImproveSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = HelpUsImprove
        kwargs['serializer_class'] = HelpUsImproveSerializer
        kwargs['item_name'] = 'HelpUsImprove'
        super().__init__(*args, **kwargs)
        
class AdminUserView(DynamicModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = CustomUser
        kwargs['serializer_class'] = AdminUserSerializer
        kwargs['item_name'] = 'CustomUser'
        super().__init__(*args, **kwargs)
