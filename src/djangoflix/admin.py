from django.contrib import admin
from .models import Account, Profile, WatchableContent


class ProfileAdmin(admin.ModelAdmin):
    fields = ["account", "profile_name"]

# Register your models here.
admin.site.register(Account)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(WatchableContent)