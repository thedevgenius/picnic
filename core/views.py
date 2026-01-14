from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.db.models import Sum

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


class DetailsPageView(TemplateView):
    template_name = "details.html"