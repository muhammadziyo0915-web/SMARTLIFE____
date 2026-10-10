from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Transaction(models.Model):
    TYPE_CHOICES = (("income", "Daromad"), ("expense", "Xarajat"))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"


class Task(models.Model):
    PRIORITY_CHOICES = [("high", "Muhim"), ("medium", "O‘rtacha"), ("low", "Oddiy")]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class GalleryImage(models.Model):
    """Foydalanuvchining shaxsiy galereya rasmlari."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="gallery_images")
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(
        upload_to="gallery/%Y/%m/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Galereya rasmi"
        verbose_name_plural = "Galereya rasmlari"

    def __str__(self):
        return self.title or f"{self.user.username} — rasm"


class Song(models.Model):
    """Foydalanuvchining shaxsiy qo'shiqlari."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="songs")
    title = models.CharField(max_length=200)
    audio = models.FileField(
        upload_to="songs/%Y/%m/",
        validators=[FileExtensionValidator(["mp3", "wav", "ogg", "m4a", "aac"])],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Qo'shiq"
        verbose_name_plural = "Qo'shiqlar"

    def __str__(self):
        return self.title


class TypingResult(models.Model):
    """Umumiy Monkeytype uslubidagi typing natijasi."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="typing_results")
    wpm = models.PositiveIntegerField(default=0)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    duration = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-wpm", "-accuracy", "created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.wpm} WPM"


class MathResult(models.Model):
    """Umumiy matematika o'yini natijasi."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="math_results")
    difficulty = models.CharField(max_length=20, default="easy")
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.score}/{self.total}"


class VocabularyResult(models.Model):
    """English vocabulary test result and per-question history."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vocabulary_results")
    total = models.PositiveIntegerField(default=20)
    correct = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    answers = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.correct}/{self.total}"
