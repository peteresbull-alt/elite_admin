from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import CustomUser, UserPhoto, People, PeoplePhoto, Notification, AdminCode
from django.utils import timezone



class AdminCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminCode
        fields = ['code']

class UserPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhoto
        fields = ['id', 'image', 'is_profile_picture', 'uploaded_at', 'order']
        read_only_fields = ['uploaded_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    photo_urls = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'date_of_birth', 'place_of_birth',
            'nationality', 'city_country', 'gender', 'full_address',
            'phone_number', 'membership_type', 'interests', 'photo_urls'
        ]

    def validate_password(self, value):
        """
        Validate password using Django's password validators
        """
        user = CustomUser(
            email=self.initial_data.get('email', ''),
            first_name=self.initial_data.get('first_name', ''),
            last_name=self.initial_data.get('last_name', '')
        )
        
        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value

    def validate(self, data):
        # Check if passwords match
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': "Passwords don't match"
            })
        return data

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        photo_urls = validated_data.pop('photo_urls', [])
        
        user = CustomUser.objects.create_user(**validated_data)
        
        # Create user photos from Cloudinary URLs
        for index, photo_url in enumerate(photo_urls):
            UserPhoto.objects.create(
                user=user,
                image=photo_url,  # Store Cloudinary URL directly
                is_profile_picture=(index == 0),
                order=index
            )
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    photos = UserPhotoSerializer(many=True, read_only=True)
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'age',
            'date_of_birth', 'place_of_birth', 'nationality', 'city_country',
            'gender', 'full_address', 'phone_number', 'membership_type',
            'interests', 'bio', 'occupation', 'education', 'height',
            'location', 'net_worth', 'looking_for', 'relationship_goals',
            'is_approved', 'verified', 'date_joined', 'profile_views',
            'matches_count', 'favorites_count', 'photos', 'profile_picture'
        ]
        read_only_fields = [
            'id', 'is_approved', 'verified', 'date_joined',
            'profile_views', 'matches_count', 'favorites_count'
        ]

    def get_profile_picture(self, obj):
        """Return Cloudinary URL for profile picture"""
        profile_photo = obj.photos.filter(is_profile_picture=True).first()
        if profile_photo:
            return str(profile_photo.image)
        first_photo = obj.photos.first()
        if first_photo:
            return str(first_photo.image)
        return None

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            # Check if user exists
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({
                    'email': 'Invalid credentials'
                })

            # Check if user is approved
            if not user.is_approved:
                raise serializers.ValidationError({
                    'non_field_errors': 'Your account is pending approval. Please wait for admin approval.'
                })

            # Authenticate user
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError({
                    'password': 'Invalid credentials'
                })

            if not user.is_active:
                raise serializers.ValidationError({
                    'non_field_errors': 'This account has been deactivated.'
                })

            data['user'] = user
            return data
        else:
            raise serializers.ValidationError({
                'non_field_errors': 'Must include "email" and "password".'
            })



class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'place_of_birth',
            'nationality', 'city_country', 'gender', 'full_address',
            'phone_number', 'interests', 'bio', 'occupation', 'education',
            'height', 'location', 'net_worth', 'looking_for',
            'relationship_goals', 'email', 'phone_number'
        ]

    def validate_email(self, value):
        user = self.instance
        if CustomUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        """
        Validate new password using Django's password validators
        """
        user = self.context['request'].user
        
        try:
            # Run Django's password validation
            validate_password(value, user=user)
        except DjangoValidationError as e:
            # Convert Django validation errors to DRF format
            raise serializers.ValidationError(list(e.messages))
        
        return value

    def validate(self, data):
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': "New passwords don't match"
            })
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    





class PeoplePhotoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PeoplePhoto
        fields = ['id', 'image', 'is_profile_picture', 'uploaded_at', 'order']
        read_only_fields = ['uploaded_at']

    def get_image(self, obj):
        """Return full Cloudinary URL"""
        if obj.image:
            image_str = str(obj.image)
            if image_str.startswith('http'):
                return image_str
            from django.conf import settings
            cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', '')
            if cloud_name:
                return f"https://res.cloudinary.com/{cloud_name}/{image_str}"
            return image_str
        return None


class PeopleListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing people (explore page cards)
    Only shows basic information
    """
    profile_picture = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()

    class Meta:
        model = People
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'age',
            'occupation', 'location', 'verified', 'profile_picture',
            'interests', 'distance', 'membership_type', "nationality",
            "city_country",
        ]

    def get_profile_picture(self, obj):
        """Return full Cloudinary URL for profile picture"""
        # First try the profile_picture field
        if obj.profile_picture:
            return self._get_full_image_url(obj.profile_picture)
        
        # Then try to get from photos
        profile_photo = obj.photos.filter(is_profile_picture=True).first()
        if profile_photo:
            return self._get_full_image_url(profile_photo.image)
        
        # Get first photo if any
        first_photo = obj.photos.first()
        if first_photo:
            return self._get_full_image_url(first_photo.image)
        
        return None

    def get_distance(self, obj):
        """Calculate distance from current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # You can get user's location from their profile
            # For now, returning a random distance for demo
            import random
            distances = [1, 2, 3, 4, 5, 6, 7]
            return f"{random.choice(distances)} miles away"
        return "N/A"

    def _get_full_image_url(self, image_field):
        """Helper method to get full Cloudinary URL"""
        if not image_field:
            return None
        image_str = str(image_field)
        if image_str.startswith('http'):
            return image_str
        from django.conf import settings
        cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', '')
        if cloud_name:
            return f"https://res.cloudinary.com/{cloud_name}/{image_str}"
        return image_str


class PeopleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed people profile view
    Shows all information including social media
    """
    photos = PeoplePhotoSerializer(many=True, read_only=True)
    profile_picture = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    social_media = serializers.SerializerMethodField()

    class Meta:
        model = People
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'age',
            'date_of_birth', 'place_of_birth', 'nationality', 'city_country',
            'gender', 'phone_number', 'bio', 'occupation', 'education',
            'height', 'location', 'net_worth', 'looking_for',
            'relationship_goals', 'interests', 'membership_type', 'verified',
            'profile_views', 'profile_picture', 'photos', 'distance',
            'images', 'social_media'
        ]

    def get_profile_picture(self, obj):
        """Return full Cloudinary URL for profile picture"""
        if obj.profile_picture:
            return self._get_full_image_url(obj.profile_picture)
        
        profile_photo = obj.photos.filter(is_profile_picture=True).first()
        if profile_photo:
            return self._get_full_image_url(profile_photo.image)
        
        first_photo = obj.photos.first()
        if first_photo:
            return self._get_full_image_url(first_photo.image)
        
        return None

    def get_images(self, obj):
        """Return all photo URLs as array"""
        images = []
        
        # Add profile picture first
        if obj.profile_picture:
            images.append(self._get_full_image_url(obj.profile_picture))
        
        # Add additional photos
        for photo in obj.photos.all():
            url = self._get_full_image_url(photo.image)
            if url and url not in images:
                images.append(url)
        
        return images if images else []

    def get_distance(self, obj):
        """Calculate distance from current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            import random
            distances = [1, 2, 3, 4, 5, 6, 7]
            return f"{random.choice(distances)} miles away"
        return "N/A"

    def get_social_media(self, obj):
        """Return social media handles"""
        social = {}
        if obj.whatsapp:
            social['whatsapp'] = obj.whatsapp
        if obj.instagram:
            social['instagram'] = obj.instagram
        if obj.twitter:
            social['twitter'] = obj.twitter
        if obj.telegram:
            social['telegram'] = obj.telegram
        return social

    def _get_full_image_url(self, image_field):
        """Helper method to get full Cloudinary URL"""
        if not image_field:
            return None
        image_str = str(image_field)
        if image_str.startswith('http'):
            return image_str
        from django.conf import settings
        cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', '')
        if cloud_name:
            return f"https://res.cloudinary.com/{cloud_name}/{image_str}"
        return image_str




class NotificationPersonSerializer(serializers.ModelSerializer):
    """Serializer for Person data in notifications"""
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = People
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'age', 'occupation', 'location', 'verified',
            'profile_picture', 'membership_type'
        ]

    def get_profile_picture(self, obj):
        """Return full Cloudinary URL for profile picture"""
        if obj.profile_picture:
            return self._get_full_image_url(obj.profile_picture)
        
        profile_photo = obj.photos.filter(is_profile_picture=True).first()
        if profile_photo:
            return self._get_full_image_url(profile_photo.image)
        
        first_photo = obj.photos.first()
        if first_photo:
            return self._get_full_image_url(first_photo.image)
        
        return None

    def _get_full_image_url(self, image_field):
        """Helper method to get full Cloudinary URL"""
        if not image_field:
            return None
        image_str = str(image_field)
        if image_str.startswith('http'):
            return image_str
        from django.conf import settings
        cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', '')
        if cloud_name:
            return f"https://res.cloudinary.com/{cloud_name}/{image_str}"
        return image_str


class NotificationSerializer(serializers.ModelSerializer):
    """Main notification serializer"""
    person = NotificationPersonSerializer(read_only=True)
    person_id = serializers.PrimaryKeyRelatedField(
        queryset=People.objects.all(),
        write_only=True,
        source='person'
    )
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'person', 'person_id', 'notification_type',
            'message', 'is_read', 'created_at', 'read_at', 'time_ago'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'read_at']

    def get_time_ago(self, obj):
        """Calculate how long ago the notification was created"""
        now = timezone.now()
        diff = now - obj.created_at
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}d ago"
        else:
            weeks = int(seconds / 604800)
            return f"{weeks}w ago"


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications (admin use)"""
    
    class Meta:
        model = Notification
        fields = [
            'user', 'person', 'notification_type', 'message'
        ]

    def validate(self, data):
        """Ensure user and person exist"""
        user = data.get('user')
        person = data.get('person')
        
        if not user.is_active:
            raise serializers.ValidationError({
                'user': 'Cannot send notification to inactive user'
            })
        
        if not person.is_active:
            raise serializers.ValidationError({
                'person': 'Cannot send notification about inactive person'
            })
        
        return data


class NotificationBulkReadSerializer(serializers.Serializer):
    """Serializer for marking multiple notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

