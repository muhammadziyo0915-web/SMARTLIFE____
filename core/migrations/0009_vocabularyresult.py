from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("core", "0008_games")]
    operations = [
        migrations.CreateModel(
            name="VocabularyResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total", models.PositiveIntegerField(default=20)),
                ("correct", models.PositiveIntegerField(default=0)),
                ("percentage", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("answers", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vocabulary_results", to="auth.user")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
