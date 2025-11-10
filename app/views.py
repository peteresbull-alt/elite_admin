from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.contrib.auth import logout
from .models import CustomUser, UserPhoto, People, Notification

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    UserPhotoSerializer,
    PeopleListSerializer, PeopleDetailSerializer,
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationBulkReadSerializer,
)
from django.db.models import Q




@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user
    POST /api/register/
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        # Get user profile data
        profile_serializer = UserProfileSerializer(user)
        
        return Response({
            'message': 'Registration successful. Your account is pending approval.',
            # 'token': token.key,
            'user': profile_serializer.data,
            'is_approved': user.is_approved
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user (only if approved)
    POST /api/login/
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Double-check approval status (already checked in serializer, but for safety)
        if not user.is_approved:
            return Response({
                'error': 'Account pending approval',
                'message': 'Your account is pending approval. Please wait for admin approval.',
                'is_approved': False
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        # Update last login
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Get user profile data
        profile_serializer = UserProfileSerializer(user)
        
        return Response({
            'message': 'Login successful',
            'token': token.key,
            'user': profile_serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user and delete token
    POST /api/logout/
    """
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        logout(request)
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get authenticated user's profile
    GET /api/profile/
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Update authenticated user's profile
    PUT/PATCH /api/profile/update/
    """
    serializer = UserUpdateSerializer(
        request.user, 
        data=request.data, 
        partial=request.method == 'PATCH'
    )
    
    if serializer.is_valid():
        serializer.save()
        
        # Return updated profile
        profile_serializer = UserProfileSerializer(request.user)
        return Response({
            'message': 'Profile updated successfully',
            'user': profile_serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password
    POST /api/password/change/
    """
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        
        # Delete old token and create new one
        request.user.auth_token.delete()
        token = Token.objects.create(user=request.user)
        
        return Response({
            'message': 'Password changed successfully',
            'token': token.key
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_user_photos(request):
    """
    Upload user photos
    POST /api/photos/upload/
    """
    files = request.FILES.getlist('photos')
    
    if not files:
        return Response({
            'error': 'No photos provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(files) > 6:
        return Response({
            'error': 'Maximum 6 photos allowed'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    photos = []
    existing_photos_count = request.user.photos.count()
    
    for index, file in enumerate(files):
        if existing_photos_count + len(photos) >= 6:
            break
            
        photo = UserPhoto.objects.create(
            user=request.user,
            image=file,
            is_profile_picture=(existing_photos_count == 0 and index == 0),
            order=existing_photos_count + index
        )
        photos.append(photo)
    
    serializer = UserPhotoSerializer(photos, many=True)
    return Response({
        'message': 'Photos uploaded successfully',
        'photos': serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_photo(request, photo_id):
    """
    Delete a user photo
    DELETE /api/photos/<photo_id>/delete/
    """
    try:
        photo = UserPhoto.objects.get(id=photo_id, user=request.user)
        photo.delete()
        
        return Response({
            'message': 'Photo deleted successfully'
        }, status=status.HTTP_200_OK)
    except UserPhoto.DoesNotExist:
        return Response({
            'error': 'Photo not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_photos(request):
    """
    Get authenticated user's photos
    GET /api/photos/
    """
    photos = request.user.photos.all()
    serializer = UserPhotoSerializer(photos, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_profile_picture(request, photo_id):
    """
    Set a photo as profile picture
    POST /api/photos/<photo_id>/set-profile/
    """
    try:
        # Remove current profile picture status
        request.user.photos.filter(is_profile_picture=True).update(
            is_profile_picture=False
        )
        
        # Set new profile picture
        photo = UserPhoto.objects.get(id=photo_id, user=request.user)
        photo.is_profile_picture = True
        photo.save()
        
        return Response({
            'message': 'Profile picture updated successfully'
        }, status=status.HTTP_200_OK)
    except UserPhoto.DoesNotExist:
        return Response({
            'error': 'Photo not found'
        }, status=status.HTTP_404_NOT_FOUND)


# Import timezone at the top of the file
from django.utils import timezone


@api_view(["GET"])
@permission_classes([AllowAny])
def validate_token(request):
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Token "):
        return Response({"detail": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

    token_key = auth_header.split(" ")[1]

    try:
        token = Token.objects.get(key=token_key)
        user = token.user
        return Response({"valid": True, "user": user.email}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({"valid": False}, status=status.HTTP_401_UNAUTHORIZED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_people_list(request):
    """
    Get list of people for explore page
    Supports filtering by membership tier, verified status, age range, etc.
    
    Query parameters:
    - membership_tier: regular, gold, platinum
    - verified_only: true/false
    - age_min: minimum age
    - age_max: maximum age
    - gender: male, female, other
    - search: search by name, occupation, location
    
    Example: GET /api/people/?verified_only=true&age_min=25&age_max=35
    """
    # Get current user's membership tier
    user_membership = request.user.membership_type
    membership_hierarchy = {'regular': 1, 'gold': 2, 'platinum': 3}
    user_level = membership_hierarchy.get(user_membership, 1)
    
    # Base queryset - only active people
    queryset = People.objects.filter(is_active=True)
    
    # Apply filters from query parameters
    membership_filter = request.GET.get('membership_tier')
    if membership_filter:
        queryset = queryset.filter(membership_type=membership_filter)
    
    verified_only = request.GET.get('verified_only', '').lower() == 'true'
    if verified_only:
        queryset = queryset.filter(verified=True)
    
    age_min = request.GET.get('age_min')
    if age_min:
        try:
            queryset = queryset.filter(age__gte=int(age_min))
        except ValueError:
            pass
    
    age_max = request.GET.get('age_max')
    if age_max:
        try:
            queryset = queryset.filter(age__lte=int(age_max))
        except ValueError:
            pass
    
    gender = request.GET.get('gender')
    if gender and gender in ['male', 'female', 'other']:
        queryset = queryset.filter(gender=gender)
    
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(occupation__icontains=search) |
            Q(location__icontains=search)
        )
    
    # Order by created_at (newest first)
    queryset = queryset.order_by('-created_at')
    
    # Serialize the data
    serializer = PeopleListSerializer(
        queryset, 
        many=True, 
        context={'request': request}
    )
    
    # Add user's membership level to response for frontend to handle access control
    return Response({
        'results': serializer.data,
        'count': queryset.count(),
        'user_membership': user_membership,
        'user_membership_level': user_level
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_person_detail(request, person_id):
    """
    Get detailed information about a specific person
    Only accessible if user has equal or higher membership tier
    
    Example: GET /api/people/1/
    """
    try:
        person = People.objects.get(id=person_id, is_active=True)
    except People.DoesNotExist:
        return Response({
            'error': 'Person not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check membership access
    user_membership = request.user.membership_type
    person_membership = person.membership_type
    
    membership_hierarchy = {'regular': 1, 'gold': 2, 'platinum': 3}
    user_level = membership_hierarchy.get(user_membership, 1)
    person_level = membership_hierarchy.get(person_membership, 1)
    
    # User must have equal or higher tier to access
    if user_level < person_level:
        return Response({
            'error': 'Access denied',
            'message': f'Upgrade to {person_membership} membership to view this profile',
            'required_membership': person_membership,
            'user_membership': user_membership,
            'locked': True
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Increment profile views
    person.profile_views += 1
    person.save(update_fields=['profile_views'])
    
    # Serialize and return data
    serializer = PeopleDetailSerializer(person, context={'request': request})
    
    return Response({
        'person': serializer.data,
        'locked': False,
        'user_membership': user_membership
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_people_stats(request):
    """
    Get statistics about people for dashboard
    
    Example: GET /api/people/stats/
    """
    user_membership = request.user.membership_type
    membership_hierarchy = {'regular': 1, 'gold': 2, 'platinum': 3}
    user_level = membership_hierarchy.get(user_membership, 1)
    
    # Get accessible people based on membership
    accessible_tiers = [tier for tier, level in membership_hierarchy.items() if level <= user_level]
    accessible_people = People.objects.filter(
        is_active=True,
        membership_type__in=accessible_tiers
    )
    
    total_people = People.objects.filter(is_active=True).count()
    verified_people = People.objects.filter(is_active=True, verified=True).count()
    
    # Count by membership tier
    regular_count = People.objects.filter(is_active=True, membership_type='regular').count()
    gold_count = People.objects.filter(is_active=True, membership_type='gold').count()
    platinum_count = People.objects.filter(is_active=True, membership_type='platinum').count()
    
    return Response({
        'total_people': total_people,
        'accessible_people': accessible_people.count(),
        'verified_people': verified_people,
        'by_tier': {
            'regular': regular_count,
            'gold': gold_count,
            'platinum': platinum_count
        },
        'user_membership': user_membership,
        'user_level': user_level
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_access_to_person(request, person_id):
    """
    Check if user can access a specific person's profile
    Returns access status without retrieving full profile
    
    Example: POST /api/people/1/check-access/
    """
    try:
        person = People.objects.get(id=person_id, is_active=True)
    except People.DoesNotExist:
        return Response({
            'error': 'Person not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    user_membership = request.user.membership_type
    person_membership = person.membership_type
    
    membership_hierarchy = {'regular': 1, 'gold': 2, 'platinum': 3}
    user_level = membership_hierarchy.get(user_membership, 1)
    person_level = membership_hierarchy.get(person_membership, 1)
    
    has_access = user_level >= person_level
    
    return Response({
        'has_access': has_access,
        'person_membership': person_membership,
        'user_membership': user_membership,
        'required_upgrade': None if has_access else person_membership
    }, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_notifications(request):
    """
    Get all notifications for authenticated user
    Supports filtering by read/unread status
    
    Query parameters:
    - is_read: true/false (filter by read status)
    - limit: number of notifications to return (default: 50)
    
    Example: GET /api/notifications/?is_read=false&limit=20
    """
    queryset = Notification.objects.filter(user=request.user)
    
    # Filter by read status if provided
    is_read_filter = request.GET.get('is_read')
    if is_read_filter is not None:
        is_read = is_read_filter.lower() == 'true'
        queryset = queryset.filter(is_read=is_read)
    
    # Apply limit
    limit = request.GET.get('limit', 50)
    try:
        limit = int(limit)
        queryset = queryset[:limit]
    except ValueError:
        queryset = queryset[:50]
    
    # Get counts
    total_count = Notification.objects.filter(user=request.user).count()
    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    serializer = NotificationSerializer(queryset, many=True)
    
    return Response({
        'notifications': serializer.data,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': total_count - unread_count
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_detail(request, notification_id):
    """
    Get details of a specific notification
    Automatically marks it as read
    
    Example: GET /api/notifications/1/
    """
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
    except Notification.DoesNotExist:
        return Response({
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Mark as read if not already
    if not notification.is_read:
        notification.mark_as_read()
    
    serializer = NotificationSerializer(notification)
    
    return Response({
        'notification': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    """
    Mark a specific notification as read
    
    Example: POST /api/notifications/1/mark-read/
    """
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
    except Notification.DoesNotExist:
        return Response({
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    notification.mark_as_read()
    
    serializer = NotificationSerializer(notification)
    
    return Response({
        'message': 'Notification marked as read',
        'notification': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_as_read(request):
    """
    Mark all user's notifications as read
    
    Example: POST /api/notifications/mark-all-read/
    """
    updated_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return Response({
        'message': f'{updated_count} notifications marked as read',
        'updated_count': updated_count
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_multiple_notifications_as_read(request):
    """
    Mark multiple notifications as read
    
    Body: {
        "notification_ids": [1, 2, 3, 4]
    }
    
    Example: POST /api/notifications/mark-multiple-read/
    """
    serializer = NotificationBulkReadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    notification_ids = serializer.validated_data['notification_ids']
    
    updated_count = Notification.objects.filter(
        id__in=notification_ids,
        user=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return Response({
        'message': f'{updated_count} notifications marked as read',
        'updated_count': updated_count
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """
    Delete a specific notification
    
    Example: DELETE /api/notifications/1/
    """
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.delete()
        
        return Response({
            'message': 'Notification deleted successfully'
        }, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return Response({
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_read_notifications(request):
    """
    Delete all read notifications for the user
    
    Example: DELETE /api/notifications/delete-all-read/
    """
    deleted_count, _ = Notification.objects.filter(
        user=request.user,
        is_read=True
    ).delete()
    
    return Response({
        'message': f'{deleted_count} notifications deleted',
        'deleted_count': deleted_count
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notification_stats(request):
    """
    Get notification statistics for the user
    
    Example: GET /api/notifications/stats/
    """
    total = Notification.objects.filter(user=request.user).count()
    unread = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    # Count by notification type
    from django.db.models import Count
    type_counts = Notification.objects.filter(
        user=request.user
    ).values('notification_type').annotate(
        count=Count('id')
    )
    
    return Response({
        'total_notifications': total,
        'unread_notifications': unread,
        'read_notifications': total - unread,
        'by_type': list(type_counts)
    }, status=status.HTTP_200_OK)


# Admin endpoints
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_notification(request):
    """
    Create a new notification (Admin only)
    
    Body: {
        "user": 1,
        "person": 2,
        "notification_type": "profile_view",
        "message": "Sarah viewed your profile"
    }
    
    Example: POST /api/notifications/create/
    """
    serializer = NotificationCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        notification = serializer.save()
        
        response_serializer = NotificationSerializer(notification)
        
        return Response({
            'message': 'Notification created successfully',
            'notification': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_bulk_notifications(request):
    """
    Send notifications to multiple users (Admin only)
    
    Body: {
        "user_ids": [1, 2, 3],
        "person": 5,
        "notification_type": "match",
        "message": "You have a new match!"
    }
    
    Example: POST /api/notifications/send-bulk/
    """
    user_ids = request.data.get('user_ids', [])
    person_id = request.data.get('person')
    notification_type = request.data.get('notification_type', 'custom')
    message = request.data.get('message')
    
    if not user_ids or not person_id or not message:
        return Response({
            'error': 'user_ids, person, and message are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        person = People.objects.get(id=person_id, is_active=True)
        users = CustomUser.objects.filter(
            id__in=user_ids,
            is_active=True
        )
        
        notifications = []
        for user in users:
            notification = Notification.objects.create(
                user=user,
                person=person,
                notification_type=notification_type,
                message=message
            )
            notifications.append(notification)
        
        return Response({
            'message': f'{len(notifications)} notifications created',
            'created_count': len(notifications)
        }, status=status.HTTP_201_CREATED)
        
    except People.DoesNotExist:
        return Response({
            'error': 'Person not found'
        }, status=status.HTTP_404_NOT_FOUND)










