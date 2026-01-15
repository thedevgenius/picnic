from django.urls import path
from .views import HomePageView, JoinPageView, DashboardView, BillPageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('join/', JoinPageView.as_view(), name='join'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('bill/', BillPageView.as_view(), name='bill'),
]
