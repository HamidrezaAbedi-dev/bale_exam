from django.contrib import admin
from .models import User

# Register your models here.

@admin.register(User)
class UserExamAdmin(admin.ModelAdmin):

    date_hierarchy='created_at'

    empty_vlaue_display = '-empty-'