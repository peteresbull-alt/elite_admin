from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserPhoto, People, PeoplePhoto




class UserPhotoInline(admin.TabularInline):
    model = UserPhoto
    extra = 1
    fields = ['image', 'is_profile_picture', 'order']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = [UserPhotoInline]
    
    list_display = [
        'email', 'first_name', 'last_name', 'membership_type',
        'is_approved', 'verified', 'is_active', 'date_joined'
    ]
    
    list_filter = [
        'is_approved', 'verified', 'is_active', 'is_staff',
        'membership_type', 'gender', 'date_joined'
    ]
    
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'date_of_birth', 'gender',
                'place_of_birth', 'nationality', 'height'
            )
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'full_address', 'city_country', 'location')
        }),
        ('Professional Information', {
            'fields': ('occupation', 'education', 'net_worth')
        }),
        ('Profile Details', {
            'fields': (
                'bio', 'interests', 'looking_for', 'relationship_goals',
                'membership_type'
            )
        }),
        ('Account Status', {
            'fields': (
                'is_approved', 'verified', 'is_active', 'is_staff',
                'is_superuser'
            )
        }),
        ('Statistics', {
            'fields': ('profile_views', 'matches_count', 'favorites_count')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login')
        }),
    )
    
    add_fieldsets = (
        ('Authentication', {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name')
        }),
        ('Account Status', {
            'fields': ('is_approved', 'is_active', 'is_staff')
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    actions = ['approve_users', 'verify_users', 'deactivate_users']
    
    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} users approved successfully.')
    approve_users.short_description = 'Approve selected users'
    
    def verify_users(self, request, queryset):
        updated = queryset.update(verified=True)
        self.message_user(request, f'{updated} users verified successfully.')
    verify_users.short_description = 'Verify selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'


@admin.register(UserPhoto)
class UserPhotoAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_profile_picture', 'order', 'uploaded_at']
    list_filter = ['is_profile_picture', 'uploaded_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['-uploaded_at']






class PeoplePhotoInline(admin.TabularInline):
    model = PeoplePhoto
    extra = 1
    fields = ('image', 'is_profile_picture', 'order')


@admin.register(People)
class PeopleAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'age', 'gender', 'membership_type',
        'verified', 'location', 'created_at'
    ]
    list_filter = [
        'membership_type', 'verified', 'gender', 'is_active', 'created_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'occupation', 'location'
    ]
    readonly_fields = ['age', 'created_at', 'updated_at', 'profile_views']
    inlines = [PeoplePhotoInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'email', 'gender', 'date_of_birth', 'age')
        }),
        ('Location', {
            'fields': ('place_of_birth', 'nationality', 'city_country', 'location', 'full_address', 'latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone_number',)
        }),
        ('Profile Details', {
            'fields': ('bio', 'occupation', 'education', 'height', 'net_worth', 'looking_for', 'relationship_goals', 'interests')
        }),
        ('Social Media', {
            'fields': ('whatsapp', 'instagram', 'twitter', 'telegram')
        }),
        ('Membership & Status', {
            'fields': ('membership_type', 'verified', 'is_active')
        }),
        ('Media', {
            'fields': ('profile_picture',)
        }),
        ('Statistics', {
            'fields': ('profile_views', 'created_at', 'updated_at')
        }),
    )


@admin.register(PeoplePhoto)
class PeoplePhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'person', 'is_profile_picture', 'order', 'uploaded_at']
    list_filter = ['is_profile_picture', 'uploaded_at']
    search_fields = ['person__first_name', 'person__last_name']





