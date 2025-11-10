from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from cloudinary.models import CloudinaryField




class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_approved', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    MEMBERSHIP_CHOICES = [
        ('regular', 'Regular'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    # Authentication fields
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    
    # Basic Information (Step 1)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Personal Details (Step 2)
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=200, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    city_country = models.CharField(max_length=200, blank=True)
    
    # Contact Information (Step 3)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    full_address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Membership & Interests (Step 4)
    membership_type = models.CharField(
        max_length=10, 
        choices=MEMBERSHIP_CHOICES, 
        default='regular'
    )
    interests = models.JSONField(default=list, blank=True)
    
    # Profile Information
    bio = models.TextField(blank=True)
    occupation = models.CharField(max_length=200, blank=True)
    education = models.CharField(max_length=200, blank=True)
    height = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    net_worth = models.CharField(max_length=50, blank=True)
    looking_for = models.CharField(max_length=100, blank=True)
    relationship_goals = models.JSONField(default=list, blank=True)
    
    # Profile Picture (main photo)
    profile_picture = CloudinaryField('image', folder='profile_pictures', blank=True, null=True)
    
    # Account Status
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Profile Stats (optional)
    profile_views = models.IntegerField(default=0)
    matches_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class UserPhoto(models.Model):
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='photos'
    )
    image = CloudinaryField('image', folder='user_photos')
    is_profile_picture = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'user_photos'
        ordering = ['order', '-is_profile_picture', '-uploaded_at']

    def __str__(self):
        return f"Photo for {self.user.email}"
    


class People(models.Model):
    """
    People model for displaying potential matches in explore page
    Similar to CustomUser but for browsable profiles
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    MEMBERSHIP_CHOICES = [
        ('regular', 'Regular'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    
    # Personal Details
    date_of_birth = models.DateField()
    age = models.IntegerField(editable=False, null=True, blank=True)
    place_of_birth = models.CharField(max_length=200, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    city_country = models.CharField(max_length=200, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    full_address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Profile Information
    bio = models.TextField(blank=True)
    occupation = models.CharField(max_length=200, blank=True)
    education = models.CharField(max_length=200, blank=True)
    height = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    net_worth = models.CharField(max_length=50, blank=True)
    looking_for = models.CharField(max_length=100, blank=True)
    relationship_goals = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    
    # Membership & Status
    membership_type = models.CharField(
        max_length=10, 
        choices=MEMBERSHIP_CHOICES, 
        default='regular'
    )
    verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Social Media Handles
    whatsapp = models.CharField(max_length=20, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    
    # Location Data (for distance calculation)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Profile Picture
    profile_picture = CloudinaryField('image', folder='people_profiles', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Stats
    profile_views = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'people'
        verbose_name = 'Person'
        verbose_name_plural = 'People'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Calculate age from date_of_birth
        if self.date_of_birth:
            today = timezone.now().date()
            self.age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        super().save(*args, **kwargs)

    def calculate_distance(self, user_lat, user_lon):
        """
        Calculate distance between this person and user's location
        Returns distance in miles
        """
        if not self.latitude or not self.longitude:
            return None
        
        from math import radians, sin, cos, sqrt, atan2
        
        # Radius of Earth in miles
        R = 3959
        
        lat1 = radians(float(user_lat))
        lon1 = radians(float(user_lon))
        lat2 = radians(float(self.latitude))
        lon2 = radians(float(self.longitude))
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        distance = R * c
        return round(distance, 1)


class PeoplePhoto(models.Model):
    """
    Additional photos for People profiles
    """
    person = models.ForeignKey(
        People, 
        on_delete=models.CASCADE, 
        related_name='photos'
    )
    image = CloudinaryField('image', folder='people_photos')
    is_profile_picture = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'people_photos'
        ordering = ['order', '-is_profile_picture', '-uploaded_at']

    def __str__(self):
        return f"Photo for {self.person.full_name}"
    

    