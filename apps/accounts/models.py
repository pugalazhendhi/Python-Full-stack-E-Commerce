from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Email is used as a unique identifier option.
    """
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone Number")
    is_verified = models.BooleanField(default=False, verbose_name="Verified Account")

    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username or self.email

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username


class UserProfile(models.Model):
    """
    Extended user profile for additional customer information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='profiles/avatars/', blank=True, null=True, verbose_name="Avatar Image")
    bio = models.TextField(max_length=500, blank=True, verbose_name="Bio")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.username}"


class Address(models.Model):
    """
    Customer shipping and billing addresses.
    """
    ADDRESS_TYPE_CHOICES = (
        ('home', 'Home'),
        ('work', 'Work / Office'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=120, verbose_name="Recipient Full Name")
    phone_number = models.CharField(max_length=20, verbose_name="Contact Phone")
    address_line1 = models.CharField(max_length=255, verbose_name="Address Line 1")
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name="Address Line 2 (Optional)")
    city = models.CharField(max_length=100, verbose_name="City")
    state = models.CharField(max_length=100, verbose_name="State / Province")
    postal_code = models.CharField(max_length=20, verbose_name="Postal / ZIP Code")
    country = models.CharField(max_length=100, default="India", verbose_name="Country")
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='home')
    is_default = models.BooleanField(default=False, verbose_name="Set as Default Address")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer Address'
        verbose_name_plural = 'Customer Addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.address_line1}, {self.city} ({self.postal_code})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure other addresses for this user are not marked default
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
