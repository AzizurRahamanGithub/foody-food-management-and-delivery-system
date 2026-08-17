from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import timedelta
import string
import random
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from import_export.admin import ImportExportActionModelAdmin
now = timezone.now()
from django.contrib import admin


class Role(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    LEARNER = 'user', 'User'


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    is_active= models.BooleanField(default=True)
    role = models.CharField(max_length=10, choices=Role.choices,
                            default=Role.LEARNER, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(
        max_length=15, unique=True, null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    photo = models.URLField(null=True, blank=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.full_name or self.phone_number or self.email or self.username

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email'], name='email_idx'),
            models.Index(fields=['username'], name='username_idx'),
            models.Index(fields=['phone_number'], name='phone_number_idx'),
            models.Index(fields=['role'], name='role_idx'),
            models.Index(fields=['created_at'], name='created_at_idx'),
        ]


class CustomUserAdmin(ImportExportActionModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'role', 'is_phone_verified', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone_number', 'full_name')


class PhoneVerification(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    otp_created_at = models.DateTimeField(auto_now_add=True)

    OTP_EXPIRY_MINUTES = 10

    def is_otp_expired(self):
        if self.otp_created_at:
            return timezone.now() > self.otp_created_at + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        return True

    def can_resend(self):
        if self.otp_created_at:
            return timezone.now() > self.otp_created_at + timedelta(seconds=60)
        return True

    def generate_otp(self):
        self.otp = ''.join(random.choices(string.digits, k=6))
        self.attempts = 0
        self.is_verified = False
        self.otp_created_at = timezone.now()
        return self.otp

    def __str__(self):
        return f"{self.phone_number} - {'verified' if self.is_verified else 'pending'}"

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(auto_now_add=True)
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    reset_token_expires = models.DateTimeField(null=True, blank=True)

    def is_otp_expired(self):
        if self.otp_created_at:
            return timezone.now() > self.otp_created_at + timedelta(minutes=10)
        return True

    def is_reset_token_expired(self):
        if self.reset_token_expires:
            return timezone.now() > self.reset_token_expires
        return True

    def generate_reset_token(self):
        self.reset_token = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=32))
        self.reset_token_expires = timezone.now() + timedelta(minutes=5)
        self.save()
        return self.reset_token

    def __str__(self):
        return f"Profile of {self.user.email}"


class ContactMessage (models.Model):
    full_name= models.CharField(max_length=200)
    email= models.EmailField()
    subject= models.CharField(max_length=300)
    message= models.TextField()
    created_at= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.full_name}-{self.subject}"
    
class HelpUsImprove(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="improving") 
    improve_message= models.TextField()
    
    def __str__(self):
        return f"{self.user.full_name}-{self.improve_message}"