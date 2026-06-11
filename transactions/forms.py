from django import forms
from django.core.exceptions import ValidationError
from .models import Customer, Transaction, CustomerNote


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

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get('mobile_number', '').strip()
        if not mobile_number:
            raise ValidationError('মোবাইল নম্বর প্রয়োজন!')

        # Check for duplicate mobile number
        existing = Customer.objects.filter(mobile_number=mobile_number)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            existing_customer = existing.first()
            raise ValidationError(
                f'❌ এই মোবাইল নম্বরটি ইতিমধ্যে "{existing_customer.name}" নামে নিবন্ধিত আছে! '
                f'একই মোবাইল নম্বর দিয়ে নতুন কাস্টমার তৈরি করা যাবে না।'
            )

        return mobile_number


class TransactionSubmissionForm(forms.ModelForm):
    """Form for Submission (Deposit) transaction"""
    class Meta:
        model = Transaction
        fields = ['amount', 'order_date', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
        }
        labels = {
            'order_date': 'তারিখ (Date)',
            'amount': 'পরিমাণ (Amount)',
            'notes': 'নোট (Notes)',
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
        fields = ['amount', 'order_date', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
        }
        labels = {
            'order_date': 'তারিখ (Date)',
            'amount': 'পরিমাণ (Amount)',
            'notes': 'নোট (Notes)',
        }


class CustomerNoteForm(forms.ModelForm):
    """Form for Customer Note"""
    class Meta:
        model = CustomerNote
        fields = ['note']
        widgets = {
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter note about this customer...'}),
        }
