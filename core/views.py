from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.db.models import Sum
from .models import Diposit, Expense, User, Settings
from .forms import DipositForm, ExpenseForm

User = get_user_model()
# Create your views here.
class HomePageView(View):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        user = request.user
        context = {}
        if user.is_authenticated:
            amount = request.user.candidate * 300
            diposits = user.diposits.all().order_by("-created_at")
            total_amount = (
                user.diposits
                    .aggregate(total=Sum("amount"))
                    .get("total") or 0
            )
            context = {
                "amount": amount,
                "diposits": diposits,
                "total_amount": total_amount,
                "participant": user.candidate,
            }
        users = User.objects.filter(is_active=True, is_paid=True)
        context["total_participants"] = users.aggregate(total=Sum("candidate")).get("total") or 0
        context["users"] = users
        return render(request, self.template_name, context)
    
PRICE_PER_PERSON = 300
MIN_PARTICIPANTS = 1

def generate_upi_url(user):
    upi_id = "dhararupam@upi"   # CHANGE THIS
    payee_name = "Office Picnic"
    note = f"Payment for Office Picnic"
    amount = user.candidate * PRICE_PER_PERSON
    upi_url = (
        "upi://pay?"
        f"pa={upi_id}&"
        f"pn={payee_name}&"
        f"am={amount}&"
        f"cu=INR&"
        f"tn={note}"
    )
    return upi_url

class JoinPageView(View):
    template_name = "join.html"

    def get(self, request, *args, **kwargs):
        context = {}
        if request.user.is_authenticated and request.user.is_paid:
            return redirect("home")
        if request.user.is_authenticated:
            amount = request.user.candidate * PRICE_PER_PERSON
            candidate = request.user.candidate
            phone = request.user.phone
            user = request.user.first_name or request.user.phone
            context = {
                "upi_url": generate_upi_url(request.user),
                "amount": amount,
                "candidate": candidate,
                "phone": phone,
                "name": user,
            }
        return render(request, self.template_name, context)


    def post(self, request, *args, **kwargs):
        phone = request.POST.get("phone")
        name = request.POST.get("name")
        candidate = int(request.POST.get("candidate", 1))
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                "first_name": name,
                "candidate": candidate,
                "is_requested": True,
            }
        )
        if user:
            if user.is_paid:
                login(request, user)
                return redirect("home")
            else:
                user.candidate = candidate
                user.is_requested = True
                user.save()
                login(request, user)
        else:
            print("Failed to create or fetch user with phone:", phone)


        amount = candidate * PRICE_PER_PERSON
        upi_url = generate_upi_url(user)
        
        return render(request, self.template_name, {
            "upi_url": upi_url,
            "amount": amount,
            "candidate": candidate,
            "phone": phone,
            "name": name,
        })

class PaymetPageView(TemplateView):
    template_name = "payment.html"

class DashboardView(View):
    template_name = "dashboard.html"
    
    def get(self, request, *args, **kwargs):
        context = {}
        total_deposit = Diposit.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0

        total_expense  = Expense.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0

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
    

class BillPageView(View):
    template_name = "bill.html"

    def get(self, request, *args, **kwargs):
        context = {}

        settings, _ = Settings.objects.get_or_create(name="default")

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