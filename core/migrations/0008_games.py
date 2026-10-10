from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0007_galleryimage_song')]
    operations = [
        migrations.CreateModel(
            name='TypingResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wpm', models.PositiveIntegerField(default=0)),
                ('accuracy', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('duration', models.PositiveIntegerField(default=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='typing_results', to='auth.user')),
            ],
            options={'ordering': ['-wpm', '-accuracy', 'created_at']},
        ),
        migrations.CreateModel(
            name='MathResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('difficulty', models.CharField(default='easy', max_length=20)),
                ('score', models.PositiveIntegerField(default=0)),
                ('total', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='math_results', to='auth.user')),
            ],
            options={'ordering': ['-score', 'created_at']},
        ),
    ]
