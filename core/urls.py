from django.urls import path
from .views import HomePageView, user_list, generate_login_link, one_time_login

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path("users/", user_list, name="user_list"),
    path("generate-login-link/<int:user_id>/", generate_login_link, name="generate_login_link"),
    path("one-time-login/<uuid:token>/", one_time_login, name="one_time_login"),
]
