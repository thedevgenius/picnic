from django.urls import path
from .views import HomePageView, DetailsPageView, JoinPageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('details/', DetailsPageView.as_view(), name='details'),
    path('join/', JoinPageView.as_view(), name='join'),
    
]
