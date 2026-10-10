from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import json

from .models import GalleryImage, MathResult, Notification, Profile, Song, Task, Transaction, TypingResult, VocabularyResult


# =========================================================
# MONEY
# =========================================================

def _money(value):
    return f"{Decimal(value or 0):,.0f}".replace(",", " ")


# =========================================================
# HOME
# =========================================================

@login_required
def home(request):

    transactions = Transaction.objects.filter(user=request.user)
    tasks_qs = Task.objects.filter(user=request.user)

    income = (
        transactions
        .filter(type="income")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    expense = (
        transactions
        .filter(type="expense")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    balance = income - expense

    completed = tasks_qs.filter(completed=True).count()
    total_tasks = tasks_qs.count()

    progress = (
        round((completed / total_tasks) * 100)
        if total_tasks
        else 0
    )

    recent_tasks = (
        tasks_qs
        .filter(completed=False)
        .order_by("deadline")[:5]
    )

    categories = list(
        transactions
        .filter(type="expense")
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:6]
    )

    context = {
        "income": income,
        "expense": expense,
        "balance": balance,

        "income_display": _money(income),
        "expense_display": _money(expense),
        "balance_display": _money(balance),

        "recent_transactions": (
            transactions
            .order_by("-created_at")[:5]
        ),

        "recent_tasks": recent_tasks,
        "categories": categories,

        "task_progress": progress,
        "total_tasks": total_tasks,
        "completed_tasks": completed,
    }

    return render(request, "home.html", context)


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        if not username or not password:
            return render(
                request,
                "register.html",
                {
                    "error": "Barcha maydonlarni to‘ldiring."
                }
            )

        if password != password2:
            return render(
                request,
                "register.html",
                {
                    "error": "Parollar bir xil emas."
                }
            )

        if len(password) < 6:
            return render(
                request,
                "register.html",
                {
                    "error": "Parol kamida 6 ta belgidan iborat bo‘lsin."
                }
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "register.html",
                {
                    "error": "Bu username band!"
                }
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        Profile.objects.create(
            user=user,
            first_name=username
        )

        login(request, user)

        return redirect("home")

    return render(request, "register.html")


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("home")

        return render(
            request,
            "login.html",
            {
                "error": "Username yoki parol xato!"
            }
        )

    return render(request, "login.html")


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    logout(request)

    return redirect("login")


# =========================================================
# ADD TRANSACTION
# =========================================================

@login_required
def add_transaction(request):

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        amount_raw = request.POST.get(
            "amount",
            ""
        ).strip()

        transaction_type = request.POST.get(
            "type",
            "expense"
        )

        category = request.POST.get(
            "category",
            "Boshqa"
        ).strip() or "Boshqa"

        try:

            amount = Decimal(amount_raw)

            if amount <= 0:
                raise InvalidOperation

        except (InvalidOperation, TypeError):

            return render(
                request,
                "add_transaction.html",
                {
                    "error": "Summani to‘g‘ri kiriting."
                }
            )

        if not title:

            return render(
                request,
                "add_transaction.html",
                {
                    "error": "Operatsiya nomini kiriting."
                }
            )

        Transaction.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            type=transaction_type,
            category=category
        )

        return redirect("transactions")

    return render(request, "add_transaction.html")


# =========================================================
# TRANSACTIONS
# =========================================================

@login_required
def transactions(request):

    data = (
        Transaction.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    search = request.GET.get(
        "search",
        ""
    ).strip()

    transaction_type = request.GET.get(
        "type",
        ""
    )

    category = request.GET.get(
        "category",
        ""
    )

    if search:
        data = data.filter(
            title__icontains=search
        )

    if transaction_type in {"income", "expense"}:
        data = data.filter(
            type=transaction_type
        )

    if category:
        data = data.filter(
            category__iexact=category
        )

    income = (
        data
        .filter(type="income")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    expense = (
        data
        .filter(type="expense")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    categories = (
        Transaction.objects
        .filter(user=request.user)
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return render(
        request,
        "transactions.html",
        {
            "transactions": data,
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "categories": categories,
            "search": search,
            "selected_type": transaction_type,
            "selected_category": category,
        }
    )


# =========================================================
# DELETE TRANSACTION
# =========================================================

@login_required
def delete_transaction(request, id):

    if request.method == "POST":

        get_object_or_404(
            Transaction,
            id=id,
            user=request.user
        ).delete()

    return redirect("transactions")


# =========================================================
# TASKS
# =========================================================

@login_required
def tasks(request):

    task_list = (
        Task.objects
        .filter(user=request.user)
        .order_by("completed", "deadline")
    )

    now = timezone.now()

    for task in task_list:

        if task.completed:

            task.deadline_status = "completed"

        elif task.deadline < now:

            task.deadline_status = "overdue"

            title = f"⏰ Muddati o‘tgan: {task.title}"

            if not Notification.objects.filter(
                user=request.user,
                title=title
            ).exists():

                Notification.objects.create(
                    user=request.user,
                    title=title,
                    message=(
                        f'“{task.title}” vazifasining '
                        f'muddati o‘tib ketdi.'
                    )
                )

        elif (
            task.deadline - now
        ).total_seconds() <= 86400:

            task.deadline_status = "soon"

            title = f"⚠️ Tez orada: {task.title}"

            if not Notification.objects.filter(
                user=request.user,
                title=title
            ).exists():

                Notification.objects.create(
                    user=request.user,
                    title=title,
                    message=(
                        f'“{task.title}” vazifasining '
                        f'muddati 24 soat ichida tugaydi.'
                    )
                )

        else:

            task.deadline_status = "normal"

    total = task_list.count()

    completed = task_list.filter(
        completed=True
    ).count()

    progress = (
        round((completed / total) * 100)
        if total
        else 0
    )

    return render(
        request,
        "tasks.html",
        {
            "tasks": task_list,
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": total - completed,
            "progress": progress,

            "high_tasks": task_list.filter(
                priority="high",
                completed=False
            ).count(),

            "medium_tasks": task_list.filter(
                priority="medium",
                completed=False
            ).count(),

            "low_tasks": task_list.filter(
                priority="low",
                completed=False
            ).count(),
        }
    )


# =========================================================
# ADD TASK
# =========================================================

@login_required
def add_task(request):

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        deadline = request.POST.get(
            "deadline"
        )

        if not title or not deadline:

            return render(
                request,
                "add_task.html",
                {
                    "error": (
                        "Vazifa nomi va "
                        "muddatni kiriting."
                    )
                }
            )

        try:
            deadline_value = datetime.fromisoformat(deadline)
            if timezone.is_naive(deadline_value):
                deadline_value = timezone.make_aware(
                    deadline_value,
                    timezone.get_current_timezone()
                )
        except (TypeError, ValueError):
            return render(
                request,
                "add_task.html",
                {
                    "error": "Muddat formati noto‘g‘ri. Sanani qaytadan tanlang."
                }
            )

        priority = request.POST.get("priority", "medium")
        if priority not in {"high", "medium", "low"}:
            priority = "medium"

        Task.objects.create(
            user=request.user,
            title=title,
            description=request.POST.get("description", "").strip(),
            deadline=deadline_value,
            priority=priority
        )

        return redirect("tasks")

    return render(request, "add_task.html")


# =========================================================
# COMPLETE TASK
# =========================================================

@login_required
def complete_task(request, id):

    if request.method == "POST":

        task = get_object_or_404(
            Task,
            id=id,
            user=request.user
        )

        task.completed = True

        task.save(
            update_fields=["completed"]
        )

    return redirect("tasks")


# =========================================================
# DELETE TASK
# =========================================================

@login_required
def delete_task(request, id):

    if request.method == "POST":

        get_object_or_404(
            Task,
            id=id,
            user=request.user
        ).delete()

    return redirect("tasks")


# =========================================================
# NOTIFICATIONS
# =========================================================

@login_required
def notifications(request):

    notification_list = (
        Notification.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "notifications.html",
        {
            "notifications": notification_list
        }
    )


# =========================================================
# READ NOTIFICATION
# =========================================================

@login_required
def read_notification(request, id):

    if request.method == "POST":

        notification = get_object_or_404(
            Notification,
            id=id,
            user=request.user
        )

        notification.is_read = True

        notification.save(
            update_fields=["is_read"]
        )

    return redirect("notifications")


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile(request):

    profile_data, _ = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        profile_data.first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        profile_data.last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        profile_data.phone = request.POST.get(
            "phone",
            ""
        ).strip()

        profile_data.bio = request.POST.get(
            "bio",
            ""
        ).strip()

        if request.FILES.get("avatar"):

            profile_data.avatar = request.FILES[
                "avatar"
            ]

        profile_data.save()

        return redirect("profile")

    return render(
        request,
        "profile.html",
        {
            "profile": profile_data
        }
    )


# =========================================================
# REPORT
# =========================================================

@login_required
def report(request):

    transactions_qs = Transaction.objects.filter(
        user=request.user
    )

    start_date = request.GET.get(
        "start_date",
        ""
    )

    end_date = request.GET.get(
        "end_date",
        ""
    )

    if start_date:

        transactions_qs = transactions_qs.filter(
            date__gte=start_date
        )

    if end_date:

        transactions_qs = transactions_qs.filter(
            date__lte=end_date
        )

    income = (
        transactions_qs
        .filter(type="income")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    expense = (
        transactions_qs
        .filter(type="expense")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    categories = list(
        transactions_qs
        .filter(type="expense")
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:8]
    )

    return render(
        request,
        "report.html",
        {
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "start_date": start_date,
            "end_date": end_date,
            "categories": categories,
        }
    )




# =========================================================
# GALEREYA
# =========================================================

@login_required
def gallery(request):
    images = GalleryImage.objects.filter(user=request.user)
    error = None

    if request.method == "POST":
        image = request.FILES.get("image")
        title = request.POST.get("title", "").strip()

        if not image:
            error = "Rasm tanlang."
        elif image.size > 10 * 1024 * 1024:
            error = "Rasm hajmi 10 MB dan oshmasin."
        else:
            GalleryImage.objects.create(
                user=request.user,
                title=title,
                image=image,
            )
            return redirect("gallery")

    return render(request, "gallery.html", {
        "images": images,
        "error": error,
    })


@login_required
def delete_gallery_image(request, id):
    if request.method == "POST":
        image = get_object_or_404(GalleryImage, id=id, user=request.user)
        image.delete()
    return redirect("gallery")


# =========================================================
# QO'SHIQLAR
# =========================================================

@login_required
def songs(request):
    song_list = Song.objects.filter(user=request.user)
    error = None

    if request.method == "POST":
        audio = request.FILES.get("audio")
        title = request.POST.get("title", "").strip()

        if not audio:
            error = "Qo'shiq faylini tanlang."
        elif not title:
            error = "Qo'shiq nomini kiriting."
        elif audio.size > 50 * 1024 * 1024:
            error = "Qo'shiq hajmi 50 MB dan oshmasin."
        else:
            Song.objects.create(
                user=request.user,
                title=title,
                audio=audio,
            )
            return redirect("songs")

    return render(request, "songs.html", {
        "songs": song_list,
        "error": error,
    })


@login_required
def delete_song(request, id):
    if request.method == "POST":
        song = get_object_or_404(Song, id=id, user=request.user)
        song.delete()
    return redirect("songs")


# =========================================================
# SMARTLIFE DATA FOR AI
# =========================================================

def _smartlife_context(user):

    transactions = Transaction.objects.filter(
        user=user
    )

    income = (
        transactions
        .filter(type="income")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    expense = (
        transactions
        .filter(type="expense")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    tasks = Task.objects.filter(
        user=user
    )

    pending = (
        tasks
        .filter(completed=False)
        .order_by("deadline")[:8]
    )

    task_lines = []

    for task in pending:

        task_lines.append(
            f"- {task.title} | "
            f"{task.deadline:%d.%m.%Y %H:%M} | "
            f"{task.get_priority_display()}"
        )

    task_text = (
        "\n".join(task_lines)
        if task_lines
        else "Hozircha ochiq vazifa yo‘q."
    )

    return (
        "Foydalanuvchining SmartLife ma'lumotlari:\n"
        f"- Balans: {income - expense:,.0f} so'm\n"
        f"- Jami daromad: {income:,.0f} so'm\n"
        f"- Jami xarajat: {expense:,.0f} so'm\n"
        f"- Bajarilmagan vazifalar:\n"
        f"{task_text}\n"
    )


# =========================================================
# API-SIZ SMARTLIFE YORDAMCHI
# =========================================================

def _local_bot_answer(user, message):
    """Internet va API kalitsiz ishlaydigan kichik SmartLife chatbot."""
    text = " ".join(message.lower().strip().split())
    data = _smartlife_context(user)
    balance = Transaction.objects.filter(user=user).filter(type="income").aggregate(total=Sum("amount"))["total"] or 0
    expense = Transaction.objects.filter(user=user).filter(type="expense").aggregate(total=Sum("amount"))["total"] or 0
    tasks = list(Task.objects.filter(user=user, completed=False).order_by("deadline")[:5])

    if any(x in text for x in ["salom", "assalomu", "hello", "hi"]):
        return "Salom! 👋 Men SmartLife yordamchisiman. Kichik savollaringizga javob beraman."
    if any(x in text for x in ["rahmat", "raxmat", "tashakkur"]):
        return "Arzimaydi! 😊 Yana savol bo‘lsa yozavering."
    if "isming" in text or "kimsan" in text or "sen kimsan" in text:
        return "Men SmartLife ichidagi kichik yordamchiman 🤖. API kalitisiz ishlayman."
    if any(x in text for x in ["balans", "hisobim", "qancha pulim", "moliyam"]):
        return f"💰 Jami daromad: {balance:,.0f} so‘m\n💸 Jami xarajat: {expense:,.0f} so‘m\n📊 Balans: {balance-expense:,.0f} so‘m".replace(",", " ")
    if any(x in text for x in ["vazifam", "vazifalar", "task", "topshiriq"]):
        if not tasks:
            return "📋 Hozircha bajarilmagan vazifangiz yo‘q. Zo‘r! 🎉"
        lines = ["📋 Bajarilmagan vazifalaringiz:"]
        for i, task in enumerate(tasks, 1):
            lines.append(f"{i}. {task.title} — {task.deadline:%d.%m.%Y %H:%M}")
        return "\n".join(lines)
    if any(x in text for x in ["reja", "kunimni", "bugun nima"]):
        return "🗓️ Bugungi mini-reja:\n1. ⭐ Eng muhim vazifani bajaring\n2. 📋 Qolgan vazifalarni ketma-ket qiling\n3. 💧 Tanaffus qiling\n4. ✅ Bajarilgan ishlarni belgilang"
    if any(x in text for x in ["tejash", "tejamkor", "pulni"]):
        return "💡 Tejash uchun 3 maslahat:\n1. Keraksiz xarajatlarni yozib boring.\n2. Xarid qilishdan oldin ro‘yxat tuzing.\n3. Har hafta kichik summa bo‘lsa ham jamg‘aring."
    if any(x in text for x in ["yordam", "nima qila olasan", "nimalar qila"]):
        return "🤖 Men quyidagilarda yordam beraman:\n• 📋 Vazifalarni ko‘rsatish\n• 💰 Moliya va balansni ko‘rsatish\n• 🗓️ Oddiy kunlik reja tuzish\n• 💡 Tejash bo‘yicha maslahat\n• 💬 Oddiy savollarga javob berish"
    if any(x in text for x in ["vaqt", "soat nechchi", "bugun sana"]):
        now = timezone.localtime()
        return f"🕐 Hozir Toshkent vaqti bilan {now:%H:%M}.\n📅 Sana: {now:%d.%m.%Y}."
    if "smartlife" in text:
        return "💙 SmartLife — vazifalar, moliya, eslatmalar va hisobotlarni bitta joyda boshqarishga yordam beradigan ilova."

    return "🤔 Bu savolni to‘liq tushunmadim. 'Yordam', 'vazifalarim', 'balansim', 'reja tuz' yoki 'tejash' deb yozib ko‘ring."


def _save_ai_message(request, message, answer):
    history = request.session.get("ai_history", [])
    history.extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ])
    request.session["ai_history"] = history[-12:]
    request.session.modified = True


@login_required
def ai_assisant(request):
    history = request.session.get("ai_history", [])
    answer = None
    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if message:
            answer = _local_bot_answer(request.user, message)
            _save_ai_message(request, message, answer)
            history = request.session.get("ai_history", [])
    return render(request, "ai_assisant.html", {"answer": answer, "error": None, "messages": history})


@login_required
def ai_chat_api(request):
    """Floating mini-chat uchun API kalitsiz JSON endpoint."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Faqat POST so‘rovi qabul qilinadi."}, status=405)
    message = request.POST.get("message", "").strip()
    if not message:
        return JsonResponse({"ok": False, "error": "Xabar bo‘sh bo‘lishi mumkin emas."}, status=400)
    if len(message) > 2000:
        return JsonResponse({"ok": False, "error": "Xabar 2000 belgidan oshmasin."}, status=400)
    answer = _local_bot_answer(request.user, message)
    _save_ai_message(request, message, answer)
    return JsonResponse({"ok": True, "answer": answer})


@login_required
def clear_ai_chat(request):
    if request.method == "POST":
        request.session["ai_history"] = []
        request.session.modified = True
    return redirect("ai_assisant")



# =========================================================
# O'YINLAR
# =========================================================

VOCAB_WORDS = [('school', 'maktab'), ('house', 'uy'), ('home', 'uy'), ('family', 'oila'), ('friend', 'do‘st'), ('teacher', 'o‘qituvchi'), ('student', 'o‘quvchi'), ('book', 'kitob'), ('pen', 'ruchka'), ('table', 'stol'), ('chair', 'stul'), ('room', 'xona'), ('door', 'eshik'), ('window', 'deraza'), ('water', 'suv'), ('food', 'ovqat'), ('bread', 'non'), ('morning', 'ertalab'), ('night', 'tun'), ('day', 'kun'), ('time', 'vaqt'), ('year', 'yil'), ('week', 'hafta'), ('month', 'oy'), ('today', 'bugun'), ('tomorrow', 'ertaga'), ('yesterday', 'kecha'), ('name', 'ism'), ('world', 'dunyo'), ('country', 'mamlakat'), ('city', 'shahar'), ('street', 'ko‘cha'), ('place', 'joy'), ('people', 'odamlar'), ('person', 'odam'), ('child', 'bola'), ('boy', 'o‘g‘il bola'), ('girl', 'qiz'), ('man', 'erkak'), ('woman', 'ayol'), ('mother', 'ona'), ('father', 'ota'), ('brother', 'aka/uka'), ('sister', 'opa/singil'), ('son', 'o‘g‘il'), ('daughter', 'qiz farzand'), ('life', 'hayot'), ('work', 'ish'), ('job', 'kasb/ish'), ('money', 'pul'), ('car', 'mashina'), ('road', 'yo‘l'), ('shop', 'do‘kon'), ('market', 'bozor'), ('class', 'sinf'), ('lesson', 'dars'), ('question', 'savol'), ('answer', 'javob'), ('problem', 'muammo'), ('idea', 'g‘oya'), ('story', 'hikoya'), ('word', 'so‘z'), ('language', 'til'), ('English', 'ingliz tili'), ('number', 'raqam/son'), ('example', 'misol'), ('way', 'yo‘l/usul'), ('thing', 'narsa'), ('part', 'qism'), ('right', 'to‘g‘ri/o‘ng'), ('left', 'chap'), ('first', 'birinchi'), ('last', 'oxirgi'), ('next', 'keyingi'), ('same', 'bir xil'), ('different', 'boshqa/turli'), ('new', 'yangi'), ('old', 'eski'), ('good', 'yaxshi'), ('bad', 'yomon'), ('big', 'katta'), ('small', 'kichik'), ('long', 'uzun'), ('short', 'qisqa'), ('high', 'baland'), ('low', 'past'), ('early', 'erta'), ('late', 'kech'), ('easy', 'oson'), ('hard', 'qiyin'), ('important', 'muhim'), ('beautiful', 'chiroyli'), ('happy', 'baxtli'), ('sad', 'xafa'), ('strong', 'kuchli'), ('weak', 'kuchsiz'), ('fast', 'tez'), ('slow', 'sekin'), ('hot', 'issiq'), ('cold', 'sovuq'), ('clean', 'toza'), ('dirty', 'iflos'), ('full', 'to‘la'), ('empty', 'bo‘sh'), ('open', 'ochiq'), ('closed', 'yopiq'), ('ready', 'tayyor'), ('busy', 'band'), ('go', 'bormoq'), ('come', 'kelmoq'), ('get', 'olmoq/ega bo‘lmoq'), ('give', 'bermoq'), ('take', 'olmoq'), ('make', 'qilmoq/yasamoq'), ('do', 'qilmoq'), ('have', 'ega bo‘lmoq'), ('be', 'bo‘lmoq'), ('become', 'bo‘lmoq/aylanmoq'), ('know', 'bilmoq'), ('think', 'o‘ylamoq'), ('want', 'xohlamoq'), ('need', 'kerak bo‘lmoq'), ('like', 'yoqtirmoq'), ('love', 'sevmoq'), ('use', 'ishlatmoq'), ('find', 'topmoq'), ('look', 'qaramoq'), ('see', 'ko‘rmoq'), ('watch', 'tomosha qilmoq'), ('hear', 'eshitmoq'), ('listen', 'tinglamoq'), ('say', 'aytmoq'), ('tell', 'aytib bermoq'), ('speak', 'gapirmoq'), ('ask', 'so‘ramoq'), ('read', 'o‘qimoq'), ('write', 'yozmoq'), ('learn', 'o‘rganmoq'), ('study', 'o‘qimoq/o‘rganmoq'), ('teach', 'o‘qitmoq'), ('remember', 'eslamoq'), ('forget', 'unutmoq'), ('understand', 'tushunmoq'), ('help', 'yordam bermoq'), ('try', 'urinmoq'), ('start', 'boshlamoq'), ('finish', 'tugatmoq'), ('keep', 'saqlamoq'), ('put', 'qo‘ymoq'), ('bring', 'olib kelmoq'), ('buy', 'sotib olmoq'), ('pay', 'to‘lamoq'), ('sell', 'sotmoq'), ('send', 'yubormoq'), ('show', 'ko‘rsatmoq'), ('move', 'harakatlanmoq/ko‘chirmoq'), ('turn', 'burilmoq/aylantirmoq'), ('play', 'o‘ynamoq'), ('run', 'yugurmoq'), ('walk', 'yurmoq'), ('sit', 'o‘tirmoq'), ('stand', 'turmoq'), ('live', 'yashamoq'), ('stay', 'qolmoq'), ('leave', 'ketmoq/tark etmoq'), ('meet', 'uchrashmoq'), ('call', 'qo‘ng‘iroq qilmoq'), ('feel', 'his qilmoq'), ('seem', 'tuyulmoq'), ('happen', 'sodir bo‘lmoq'), ('believe', 'ishonmoq'), ('hope', 'umid qilmoq'), ('mean', 'anglatmoq'), ('change', 'o‘zgartirmoq'), ('begin', 'boshlamoq'), ('stop', 'to‘xtatmoq'), ('follow', 'ergashmoq'), ('lead', 'yetaklamoq'), ('create', 'yaratmoq'), ('build', 'qurmoq'), ('grow', 'o‘smoq'), ('eat', 'yemoq'), ('drink', 'ichmoq'), ('sleep', 'uxlamoq'), ('wake', 'uyg‘onmoq'), ('cook', 'ovqat pishirmoq'), ('wash', 'yuvmoq'), ('wear', 'kiymoq'), ('drive', 'haydamoq'), ('travel', 'sayohat qilmoq'), ('visit', 'tashrif buyurmoq'), ('office', 'ofis'), ('company', 'kompaniya'), ('business', 'biznes'), ('team', 'jamoa'), ('group', 'guruh'), ('game', 'o‘yin'), ('music', 'musiqa'), ('movie', 'film'), ('picture', 'rasm'), ('phone', 'telefon'), ('computer', 'kompyuter'), ('internet', 'internet'), ('message', 'xabar'), ('email', 'elektron pochta'), ('website', 'veb-sayt'), ('line', 'chiziq'), ('page', 'sahifa'), ('air', 'havo'), ('sun', 'quyosh'), ('rain', 'yomg‘ir'), ('wind', 'shamol'), ('tree', 'daraxt'), ('flower', 'gul'), ('animal', 'hayvon'), ('dog', 'it'), ('cat', 'mushuk'), ('bird', 'qush'), ('head', 'bosh'), ('hand', 'qo‘l'), ('eye', 'ko‘z'), ('face', 'yuz'), ('hair', 'soch'), ('body', 'tana'), ('heart', 'yurak'), ('health', 'sog‘liq'), ('doctor', 'shifokor'), ('hospital', 'kasalxona'), ('one', 'bir'), ('two', 'ikki'), ('three', 'uch'), ('four', 'to‘rt'), ('five', 'besh'), ('six', 'olti'), ('seven', 'yetti'), ('eight', 'sakkiz'), ('nine', 'to‘qqiz'), ('ten', 'o‘n'), ('more', 'ko‘proq'), ('less', 'kamroq'), ('many', 'ko‘p'), ('few', 'oz'), ('all', 'hamma'), ('some', 'ba’zi'), ('any', 'biror/har qanday'), ('each', 'har bir'), ('every', 'har bir/har safar'), ('another', 'yana bir/boshqa'), ('who', 'kim'), ('what', 'nima'), ('where', 'qayerda'), ('when', 'qachon'), ('why', 'nega'), ('how', 'qanday'), ('which', 'qaysi'), ('whose', 'kimning'), ('because', 'chunki'), ('if', 'agar'), ('and', 'va'), ('or', 'yoki'), ('but', 'lekin'), ('so', 'shuning uchun'), ('also', 'ham/shuningdek'), ('then', 'keyin'), ('before', 'oldin'), ('after', 'keyin'), ('with', 'bilan'), ('without', 'siz'), ('in', 'ichida'), ('on', 'ustida'), ('under', 'ostida'), ('over', 'ustida/yuqorida'), ('from', 'dan'), ('to', 'ga'), ('for', 'uchun'), ('about', 'haqida'), ('near', 'yaqinida'), ('between', 'orasida'), ('my', 'mening'), ('your', 'sening/sizning'), ('his', 'uning (erkak)'), ('her', 'uning (ayol)'), ('our', 'bizning'), ('their', 'ularning'), ('this', 'bu'), ('that', 'u/ana u'), ('these', 'bular'), ('those', 'anavilar'), ('can', 'qila olmoq'), ('could', 'qila olardi'), ('will', 'bo‘ladi'), ('would', 'bo‘lardi'), ('should', 'kerak'), ('must', 'shart'), ('may', 'mumkin'), ('might', 'ehtimol'), ('always', 'har doim'), ('never', 'hech qachon'), ('often', 'tez-tez'), ('sometimes', 'ba’zan')]


def _vocab_question_set():
    import random
    selected = random.sample(VOCAB_WORDS, 20)
    questions = []
    for en, uz in selected:
        wrongs = [x[1] for x in random.sample([w for w in VOCAB_WORDS if w[0] != en and w[1] != uz], 2)]
        options = [uz] + wrongs
        random.shuffle(options)
        questions.append({"word": en, "options": options, "answer": uz})
    return questions


@login_required
def vocabulary_game(request):
    if request.method == "POST":
        try:
            submitted = json.loads(request.POST.get("answers", "[]"))
            questions = request.session.get("vocab_questions", [])
            if not questions or not isinstance(submitted, list) or len(submitted) != len(questions):
                return JsonResponse({"ok": False, "error": "Test sessiyasi topilmadi. Testni qaytadan boshlang."}, status=400)
            details=[]; correct=0
            for q, selected in zip(questions, submitted):
                selected = str(selected) if selected is not None else ""
                ok = selected == q["answer"]
                correct += int(ok)
                details.append({"word": q["word"], "correct_answer": q["answer"], "selected": selected, "is_correct": ok})
            total=len(questions); pct=round(correct/total*100,2) if total else 0
            result=VocabularyResult.objects.create(user=request.user,total=total,correct=correct,percentage=pct,answers=details)
            request.session.pop("vocab_questions", None)
            request.session.modified=True
            return JsonResponse({"ok": True, "correct": correct, "total": total, "percentage": pct, "result_id": result.id})
        except (TypeError, ValueError, json.JSONDecodeError):
            return JsonResponse({"ok": False, "error": "Natija ma’lumotlari noto‘g‘ri."}, status=400)

    questions = _vocab_question_set()
    request.session["vocab_questions"] = questions
    request.session.modified=True
    history=VocabularyResult.objects.filter(user=request.user)
    all_leaders=VocabularyResult.objects.select_related("user").order_by("-percentage", "-correct", "created_at")
    best_by_user={}
    for item in all_leaders:
        if item.user_id not in best_by_user:
            best_by_user[item.user_id]=item
    leaders=list(best_by_user.values())[:10]
    public_questions=[{"word":q["word"],"options":q["options"],"answer":q["answer"]} for q in questions]
    return render(request,"vocabulary_game.html",{"questions":public_questions,"history":history,"leaders":leaders,"word_count":len(VOCAB_WORDS)})


@login_required
def vocabulary_history(request):
    results=VocabularyResult.objects.filter(user=request.user)
    return render(request,"vocabulary_history.html",{"results":results})


@login_required
def vocabulary_result_detail(request, id):
    result=get_object_or_404(VocabularyResult,user=request.user,id=id)
    return render(request,"vocabulary_result_detail.html",{"result":result})


@login_required
def calculator(request):
    return render(request,"calculator.html")


@login_required
def games(request):
    typing_leaders = TypingResult.objects.select_related("user").order_by("-wpm", "-accuracy", "created_at")[:10]
    math_leaders = MathResult.objects.select_related("user").order_by("-score", "created_at")[:10]
    all_vocab = VocabularyResult.objects.select_related("user").order_by("-percentage", "-correct", "created_at")
    best_by_user = {}
    for item in all_vocab:
        if item.user_id not in best_by_user:
            best_by_user[item.user_id] = item
    vocab_leaders = list(best_by_user.values())[:10]
    return render(request, "games.html", {"typing_leaders": typing_leaders, "math_leaders": math_leaders, "vocab_leaders": vocab_leaders})


@login_required
def typing_game(request):
    if request.method == "POST":
        try:
            wpm = max(0, min(int(request.POST.get("wpm", 0)), 500))
            accuracy = max(0, min(float(request.POST.get("accuracy", 0)), 100))
            duration = int(request.POST.get("duration", 30))
            if duration not in (15, 30, 60):
                duration = 30
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": "Natija noto'g'ri."}, status=400)
        TypingResult.objects.create(user=request.user, wpm=wpm, accuracy=accuracy, duration=duration)
        return JsonResponse({"ok": True})
    leaders = TypingResult.objects.select_related("user").order_by("-wpm", "-accuracy", "created_at")[:20]
    return render(request, "typing_game.html", {"leaders": leaders})


@login_required
def math_game(request):
    import random
    difficulty = request.GET.get("difficulty", request.POST.get("difficulty", "easy"))
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "easy"

    if request.method == "POST" and request.POST.get("action") == "finish":
        try:
            score = max(0, int(request.POST.get("score", 0)))
            total = max(0, int(request.POST.get("total", 0)))
        except (TypeError, ValueError):
            score, total = 0, 0
        MathResult.objects.create(user=request.user, difficulty=difficulty, score=score, total=total)
        return JsonResponse({"ok": True})

    limits = {"easy": (1, 9), "medium": (2, 25), "hard": (5, 99)}
    max_num = limits[difficulty][1]
    ops = ["+", "-"] if difficulty == "easy" else ["+", "-", "×", "÷"]
    a, b = random.randint(1, max_num), random.randint(1, max_num)
    op = random.choice(ops)
    if op == "-" and b > a: a, b = b, a
    if op == "÷":
        b = random.randint(1, max_num)
        answer = random.randint(1, max_num)
        a = b * answer
    elif op == "+": answer = a + b
    elif op == "-": answer = a - b
    else: answer = a * b
    request.session["math_current"] = {"a": a, "b": b, "op": op, "answer": answer, "difficulty": difficulty}
    leaders = MathResult.objects.select_related("user").order_by("-score", "created_at")[:20]
    return render(request, "math_game.html", {"question": f"{a} {op} {b}", "difficulty": difficulty, "leaders": leaders})
