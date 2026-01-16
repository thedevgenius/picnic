from django.contrib import admin
from .models import User, Diposit, Expense, Settings
# Register your models here.
admin.site.register(User)
admin.site.register(Diposit)
admin.site.register(Expense)
admin.site.register(Settings)