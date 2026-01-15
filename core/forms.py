# forms.py
from django import forms
from .models import Diposit, Expense 

class DipositForm(forms.ModelForm):
    class Meta:
        model = Diposit
        fields = ['user', 'amount']


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense 
        fields = ['user', 'title', 'amount', 'remark']
