from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("transactions/", views.transactions, name="transactions"),
    path("transactions/add/", views.add_transaction, name="add_transaction"),
    path("transactions/<int:id>/delete/", views.delete_transaction, name="delete_transaction"),

    path("tasks/", views.tasks, name="tasks"),
    path("tasks/add/", views.add_task, name="add_task"),
    path("tasks/<int:id>/complete/", views.complete_task, name="complete_task"),
    path("tasks/<int:id>/delete/", views.delete_task, name="delete_task"),

    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:id>/read/", views.read_notification, name="read_notification"),

    path("profile/", views.profile, name="profile"),
    path("report/", views.report, name="report"),

    path("gallery/", views.gallery, name="gallery"),
    path("gallery/<int:id>/delete/", views.delete_gallery_image, name="delete_gallery_image"),

    path("songs/", views.songs, name="songs"),
    path("songs/<int:id>/delete/", views.delete_song, name="delete_song"),

    path("games/", views.games, name="games"),
    path("games/typing/", views.typing_game, name="typing_game"),
    path("games/math/", views.math_game, name="math_game"),
    path("games/vocabulary/", views.vocabulary_game, name="vocabulary_game"),
    path("games/vocabulary/history/", views.vocabulary_history, name="vocabulary_history"),
    path("games/vocabulary/result/<int:id>/", views.vocabulary_result_detail, name="vocabulary_result_detail"),
    path("games/calculator/", views.calculator, name="calculator"),

    path("ai/", views.ai_assisant, name="ai_assisant"),
    path("ai/chat/", views.ai_chat_api, name="ai_chat_api"),
    path("ai/clear/", views.clear_ai_chat, name="clear_ai_chat"),
]