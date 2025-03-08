from django.contrib import admin
from django.contrib.auth.models import User
from .models import Profile

# Mix Profile Info Into User Info
class ProfileInline(admin.StackedInline):
    model = Profile

# Extend User Model
class UserAdmin(admin.ModelAdmin):
    model = User
    # Display fields in admin page
    fields = ["username"]
    inlines = [ProfileInline]

# Unregister Initial User
admin.site.unregister(User)

# Re-register User and Profile
admin.site.register(User, UserAdmin)




