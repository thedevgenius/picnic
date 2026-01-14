from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden
from .models import OneTimeLoginToken
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
                "total_amount": total_amount
            }
        return render(request, self.template_name, context)



@staff_member_required
def user_list(request):
    users = User.objects.filter(is_active=True).exclude(is_superuser=True).order_by("-date_joined")
    return render(request, "user_list.html", {"users": users})


@staff_member_required
def generate_login_link(request, user_id):
    user = get_object_or_404(User, id=user_id)

    token = OneTimeLoginToken.create_token(user)

    login_url = request.build_absolute_uri(
        f"/one-time-login/{token.token}/"
    )

    return render(request, "share_login_link.html", {
        "user": user,
        "login_url": login_url
    })

def one_time_login(request, token):
    token_obj = get_object_or_404(
        OneTimeLoginToken,
        token=token,
        is_used=False
    )

    if not token_obj.is_valid():
        return HttpResponseForbidden("Link expired or already used")

    token_obj.is_used = True
    token_obj.save(update_fields=["is_used"])

    login(request, token_obj.user)
    return redirect("home")


class DetailsPageView(TemplateView):
    template_name = "details.html"