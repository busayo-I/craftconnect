from django.db import models
from django.contrib.auth.hashers import make_password

# Trade categories (Dynamic)
class TradeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# Artisan Model
class Artisan(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)
    email_address = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    trade_category = models.ForeignKey(TradeCategory, on_delete=models.SET_NULL, null=True)
    location = models.CharField(max_length=100)
    language = models.CharField(max_length=50)
    bio = models.TextField(blank=True, null=True)
    business_name = models.CharField(max_length=150, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Hash password before saving
        if not self.pk:  #hash only on creation
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.trade_category}"


# Client Model
class Client(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)
    email_address = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    language = models.CharField(max_length=50)
    bio = models.TextField(blank=True, null=True)
    business_name = models.CharField(max_length=150, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

