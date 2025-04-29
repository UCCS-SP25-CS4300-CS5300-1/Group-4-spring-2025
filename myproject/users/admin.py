from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import Profile, Resume

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['avatar', 'whitelisted_for_ai', 'industry_preference', 'location_preference', 'remote_preference', 'salary_min_preference']

class CustomUserAdmin(BaseUserAdmin):
    model = User
    inlines = [ProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'last_login', 'get_ai_status')
    list_filter = ('is_staff', 'is_active', 'date_joined', 'last_login', 'profile__whitelisted_for_ai')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = ['make_active', 'make_inactive', 'make_staff', 'remove_staff', 'whitelist_for_ai', 'remove_ai_whitelist']

    def get_ai_status(self, obj):
        try:
            return "Whitelisted" if obj.profile.whitelisted_for_ai else "Not Whitelisted"
        except Profile.DoesNotExist:
            return '-'
    get_ai_status.short_description = 'AI Access'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected users as active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected users as inactive"

    def make_staff(self, request, queryset):
        queryset.update(is_staff=True)
    make_staff.short_description = "Give staff privileges to selected users"

    def remove_staff(self, request, queryset):
        queryset.update(is_staff=False)
    remove_staff.short_description = "Remove staff privileges from selected users"

    def whitelist_for_ai(self, request, queryset):
        for user in queryset:
            Profile.objects.filter(user=user).update(whitelisted_for_ai=True)
    whitelist_for_ai.short_description = "Grant AI access to selected users"

    def remove_ai_whitelist(self, request, queryset):
        for user in queryset:
            if not user.is_superuser:  # Don't remove whitelist from superusers
                Profile.objects.filter(user=user).update(whitelisted_for_ai=False)
    remove_ai_whitelist.short_description = "Remove AI access from selected users"

class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_at', 'get_resume_link')
    list_filter = ('uploaded_at',)
    ordering = ('-uploaded_at',)

    def get_resume_link(self, obj):
        if (obj.resume):
            return format_html('<a href="{}" target="_blank">View Resume</a>', obj.resume.url)
        return '-'
    get_resume_link.short_description = 'Resume'

admin.site.unregister(User)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Resume, ResumeAdmin)




