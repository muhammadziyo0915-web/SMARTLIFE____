from django.contrib import admin
from .models import GalleryImage, Notification, Profile, Song, Task, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'title',
        'amount',
        'type',
        'category',
        'date',
    )

    list_filter = (
        'type',
        'category',
        'date',
    )

    search_fields = (
        'title',
        'category',
        'user__username',
    )






@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'title',
        'deadline',
        'completed',
        'created_at',
    )

    list_filter = (
        'completed',
        'deadline',
    )

    search_fields = (
        'title',
        'user__username',
    )



@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'title',
        'is_read',
        'created_at',
    )

    list_filter = (
        'is_read',
        'created_at',
    )

    search_fields = (
        'title',
        'message',
        'user__username',
    )


# =======================================================




@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'first_name',
        'last_name',
        'phone',
        'created_at',
    )

    search_fields = (
        'user__username',
        'first_name',
        'last_name',
        'phone',
    )


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "created_at")
    search_fields = ("title", "user__username")
    list_filter = ("created_at",)


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "created_at")
    search_fields = ("title", "user__username")
    list_filter = ("created_at",)

from .models import VocabularyResult
admin.site.register(VocabularyResult)
