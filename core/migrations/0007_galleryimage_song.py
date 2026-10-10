from django.conf import settings
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0006_alter_notification_id_alter_profile_id_alter_task_id_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="GalleryImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=200)),
                ("image", models.ImageField(
                    upload_to="gallery/%Y/%m/",
                    validators=[django.core.validators.FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="gallery_images", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Galereya rasmi",
                "verbose_name_plural": "Galereya rasmlari",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Song",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("audio", models.FileField(
                    upload_to="songs/%Y/%m/",
                    validators=[django.core.validators.FileExtensionValidator(["mp3", "wav", "ogg", "m4a", "aac"])],
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="songs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Qo'shiq",
                "verbose_name_plural": "Qo'shiqlar",
                "ordering": ["-created_at"],
            },
        ),
    ]
