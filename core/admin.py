from django.contrib import admin
from .models import User, Diposit, Expense 
# Register your models here.
admin.site.register(User)
admin.site.register(Diposit)
admin.site.register(Expense )