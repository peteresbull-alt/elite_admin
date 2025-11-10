from django.urls import path
from . import views

urlpatterns = [

    path('verify-code/', views.VerifyAdminCodeView.as_view(), name='verify-admin-code'),

    path("validate-token/", views.validate_token, name="validate-token"),
    # Authentication
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    
    # Profile
    path('profile/', views.get_user_profile, name='get_profile'),
    path('profile/update/', views.update_user_profile, name='update_profile'),
    
    # Password
    path('password/change/', views.change_password, name='change_password'),
    
    # Photos
    path('photos/', views.get_user_photos, name='get_photos'),
    path('photos/upload/', views.upload_user_photos, name='upload_photos'),
    path('photos/<int:photo_id>/delete/', views.delete_user_photo, name='delete_photo'),
    path('photos/<int:photo_id>/set-profile/', views.set_profile_picture, name='set_profile_picture'),

    # Get list of people with optional filters
    path('people/', views.get_people_list, name='get_people_list'),
    
    # Get detailed information about a specific person
    path('people/<int:person_id>/', views.get_person_detail, name='get_person_detail'),
    
    # Check if user can access a person's profile
    path('people/<int:person_id>/check-access/', views.check_access_to_person, name='check_access'),
    
    # Get statistics about people
    path('people/stats/', views.get_people_stats, name='get_people_stats'),


    # NOTIFICATION

    path('notifications/', views.get_user_notifications, name='get_notifications'),
    path('notifications/stats/', views.get_notification_stats, name='notification_stats'),
    path('notifications/<int:notification_id>/', views.get_notification_detail, name='notification_detail'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_as_read, name='mark_notification_read'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/mark-all-read/', views.mark_all_notifications_as_read, name='mark_all_read'),
    path('notifications/mark-multiple-read/', views.mark_multiple_notifications_as_read, name='mark_multiple_read'),
    path('notifications/delete-all-read/', views.delete_all_read_notifications, name='delete_all_read'),
    
    # Admin endpoints
    path('notifications/create/', views.create_notification, name='create_notification'),
    path('notifications/send-bulk/', views.send_bulk_notifications, name='send_bulk_notifications'),
]