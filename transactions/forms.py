from django import forms
from .models import Customer, Transaction


class CustomerForm(forms.ModelForm):
    """Form for Customer model"""
    class Meta:
        model = Customer
        fields = ['name', 'mobile_number', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
        }


class TransactionSubmissionForm(forms.ModelForm):
    """Form for Submission (Deposit) transaction"""
    class Meta:
        model = Transaction
        fields = ['amount', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
        }


class TransactionPurchaseForm(forms.ModelForm):
    """Form for Purchase transaction"""
    class Meta:
        model = Transaction
        fields = ['notes', 'order_date', 'delivery_date']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class TransactionWithdrawalForm(forms.ModelForm):
    """Form for Withdrawal transaction"""
    class Meta:
        model = Transaction
        fields = ['amount', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
        }