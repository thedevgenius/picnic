from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView
from django.contrib.auth import login, get_user_model
from django.db.models import Sum

from .models import Diposit, Expense, User, Settings
from .forms import DipositForm, ExpenseForm

User = get_user_model()
PRICE_PER_PERSON = 300
MIN_PARTICIPANTS = 1

def get_total_expense():
    total_expense  = Expense.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    return total_expense

def get_total_deposit():
    total_deposit = Diposit.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    return total_deposit

def get_total_participants():
    users = User.objects.filter(is_active=True, is_paid=True)
    total_participants = users.aggregate(
        total=Sum("candidate")
    ).get("total") or 0
    return total_participants


# Create your views here.
class HomePageView(View):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        phone = request.POST.get("phone")
        user, created = User.objects.get_or_create(
            phone=phone,
        )
        if user:
            if user.is_paid:
                login(request, user)
                return redirect("dashboard")
            else:
                user.save()
                login(request, user)
        return redirect("join")

class JoinPageView(View):
    template_name = "join.html"

    def get(self, request, *args, **kwargs):
        context = {}
        if not request.user.is_authenticated:
            return redirect("home")
        if request.user.is_authenticated and request.user.is_paid:
            return redirect("home")
        if request.user.is_authenticated:
            amount = request.user.candidate * PRICE_PER_PERSON
            candidate = request.user.candidate
            phone = request.user.phone
            
            context = {
                "amount": amount,
                "candidate": candidate,
                "phone": phone,
            }
        return render(request, self.template_name, context)


    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        candidate = int(request.POST.get("candidate", 1))
        user = request.user
        user.first_name = name
        user.candidate = candidate
        user.save()
        return redirect("pay")

class PaymetPageView(View):
    template_name = "pay.html"

    def get(self, request, *args, **kwargs):
        context = {}
        if not request.user.is_authenticated:
            return redirect("home")
        if request.user.is_authenticated and request.user.is_paid:
            return redirect("dashboard")
        if request.user.is_authenticated:
            amount = request.user.candidate * PRICE_PER_PERSON
            candidate = request.user.candidate
            phone = request.user.phone
            user = request.user.first_name or request.user.phone
            context = {
                "amount": amount,
                "candidate": candidate,
                "phone": phone,
                "name": user,
            }
        return render(request, self.template_name, context)

class MyAccountPageView(View):
    template_name = "account.html"

    def get(self, request, *args, **kwargs):
        context = {}
        if not request.user.is_authenticated:
            return redirect("home")
        if request.user.is_authenticated:
            diposits = request.user.diposits.all().order_by("-created_at")
            users = User.objects.filter(is_active=True, is_paid=True).order_by("first_name")
            total_participants = get_total_participants()
            total_amount = (
                diposits
                .aggregate(total=Sum("amount"))
                .get("total") or 0
            )
            total_expense  = get_total_expense()
            settings, _ = Settings.objects.get_or_create(name="default")
            if settings.is_calculated:
                adjusted_amount = round(settings.adjusted_amount)
                per_person_amount = (
                    round((total_expense - adjusted_amount) / total_participants)
                    if total_participants > 0 else 0
                )
                user_total = round(per_person_amount * request.user.candidate)
                balance = round(user_total - total_amount)
            else:
                adjusted_amount = 0
                per_person_amount = 0
                user_total = 0
                balance = 0

            context = {
                "diposits": diposits,
                "total_amount": total_amount,
                "participant": request.user.candidate,
                "total_participants": total_participants,
                "users": users,
                "adjusted_amount": adjusted_amount,
                "per_person_amount": per_person_amount,
                "user_total": user_total,
                "balance": balance,
                "settings": settings,
            }

        return render(request, self.template_name, context)

class DashboardView(View):
    template_name = "dashboard.html"
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect("home")
        settings, _ = Settings.objects.get_or_create(name="default")
        context = {}
        total_deposit = Diposit.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0

        total_expense  = Expense.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        if settings:
            context['adjusted_amount'] = settings.adjusted_amount

        context.update({
            'total_deposit': total_deposit,
            'total_expense': total_expense,
            'balance': total_deposit - total_expense,
            'deposit_form': DipositForm(),
            'expense_form': ExpenseForm(),
            'deposits': Diposit.objects.select_related('user').order_by('-created_at'),
            'expenses': Expense.objects.select_related('user').order_by('-created_at'),
        })
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if 'add_deposit' in request.POST:
            form = DipositForm(request.POST)
            if form.is_valid():
                form.save()

        elif 'add_expense' in request.POST:
            form = ExpenseForm(request.POST)
            if form.is_valid():
                form.save()

        elif 'calculate' in request.POST:
            adjusted_amount = request.POST.get('adjusted_amount')
            settings, _ = Settings.objects.get_or_create(name="default")
            if settings:
                settings.adjusted_amount = adjusted_amount
                settings.is_calculated = True
                settings.save()
                return redirect('bill')
            return redirect('dashboard')
        
        elif 'reset_calculation' in request.POST:
            settings, _ = Settings.objects.get_or_create(name="default")
            if settings:
                settings.is_calculated = False
                settings.adjusted_amount = 0.00
                settings.save()
                print("Calculation reset successfully.")
            

        return redirect('dashboard')
    
class BillPageView(View):
    template_name = "bill.html"

    def get(self, request, *args, **kwargs):
        context = {}
        settings, _ = Settings.objects.get_or_create(name="default")
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('home')
        if not settings.is_calculated:
            return redirect('dashboard')
        
        users = User.objects.filter(is_active=True, is_paid=True)

        total_participants = users.aggregate(
            total=Sum("candidate")
        ).get("total") or 0

        total_expense  = Expense.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0

        total_amount = total_expense

        adjusted_amount = round(settings.adjusted_amount)

        per_person_amount = (
            round((total_amount - adjusted_amount) / total_participants)
            if total_participants > 0 else 0
        )

        user_bills = []
        for user in users:
            user_total = round(per_person_amount * user.candidate)

            user_diposits = round(
                user.diposits.aggregate(total=Sum("amount")).get("total") or 0
            )

            balance = round(user_total - user_diposits)

            user_bills.append({
                "user": user,
                "total": user_total,
                "diposits": user_diposits,
                "balance": balance,
            })

        context.update({
            "user_bills": user_bills,
            "total_participants": total_participants,
            "total_amount": total_amount,
            "adjusted_amount": adjusted_amount,
            "per_person_amount": per_person_amount,
        })

        return render(request, self.template_name, context)

class GalleryPageView(TemplateView):
    template_name = "gallery.html"