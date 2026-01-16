from django.urls import path
from .views import HomePageView, JoinPageView, DashboardView, BillPageView, PaymetPageView, MyAccountPageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('join/', JoinPageView.as_view(), name='join'),
    path('pay/', PaymetPageView.as_view(), name='pay'),
    path('account/', MyAccountPageView.as_view(), name='account'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('bill/', BillPageView.as_view(), name='bill'),
]
