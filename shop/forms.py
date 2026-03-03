from django import forms
from decimal import InvalidOperation
from .models import Order, InventoryProduct, Invoice, Payment, OrderPayment


def bangla_to_english_number(text):
    """বাংলা সংখ্যা থেকে ইংরেজি সংখ্যায় রূপান্তর"""
    bangla_digits = {
        '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
        '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
    }

    if not text:
        return text

    result = str(text)
    for bangla, english in bangla_digits.items():
        result = result.replace(bangla, english)
    return result


class OrderForm(forms.ModelForm):
    """অর্ডার ফর্ম - বাংলা সংখ্যা সাপোর্ট সহ"""

    # CharField হিসেবে override করা যাতে বাংলা সংখ্যা লেখা যায়
    total_price = forms.CharField(
        label='মোট মূল্য',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ১০০০ বা 1000',
            'autocomplete': 'off',
            'inputmode': 'text',
        })
    )

    cash_paid = forms.CharField(
        label='নগদ পরিশোধ',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ৫০০ বা 500',
            'autocomplete': 'off',
            'inputmode': 'text',
        })
    )

    class Meta:
        model = Order
        fields = [
            'customer_name', 'mobile_number', 'product_name',
            'product_description', 'total_price', 'cash_paid',
            'order_date', 'delivery_date', 'status', 'delivery_status'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ক্রেতার নাম লিখুন'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control bangla-number-input',
                'placeholder': 'উদাহরণ: ০১৭১২৩৪৫৬৭৮ বা 01712345678',
                'autocomplete': 'off',
                'inputmode': 'text',
            }),
            'product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'পণ্যের নাম লিখুন'
            }),
            'product_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'পণ্যের বিস্তারিত বিবরণ লিখুন'
            }),
            'order_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'delivery_status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean_total_price(self):
        """মোট মূল্য ক্লিন করা - বাংলা সংখ্যা সাপোর্ট"""
        total_price = self.cleaned_data.get('total_price')
        if total_price:
            # বাংলা সংখ্যা থেকে ইংরেজি সংখ্যায় রূপান্তর
            converted = bangla_to_english_number(str(total_price).strip())
            # Remove any extra spaces or commas
            converted = converted.replace(',', '').replace(' ', '')
            try:
                return float(converted)
            except ValueError:
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন (উদাহরণ: ১০০০ বা 1000)')
        return 0

    def clean_cash_paid(self):
        """নগদ পরিশোধ ক্লিন করা - বাংলা সংখ্যা সাপোর্ট"""
        cash_paid = self.cleaned_data.get('cash_paid')
        if cash_paid:
            # বাংলা সংখ্যা থেকে ইংরেজি সংখ্যায় রূপান্তর
            converted = bangla_to_english_number(str(cash_paid).strip())
            # Remove any extra spaces or commas
            converted = converted.replace(',', '').replace(' ', '')
            try:
                return float(converted)
            except ValueError:
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন (উদাহরণ: ৫০০ বা 500)')
        return 0

    def clean_mobile_number(self):
        """মোবাইল নাম্বার ক্লিন করা - বাংলা সংখ্যা সাপোর্ট"""
        mobile = self.cleaned_data.get('mobile_number')
        if mobile:
            # বাংলা সংখ্যা থেকে ইংরেজি সংখ্যায় রূপান্তর
            converted = bangla_to_english_number(str(mobile).strip())
            return converted
        return mobile



class InventoryProductForm(forms.ModelForm):
    """ইনভেন্টরি পণ্য ফর্ম"""

    price_per_unit = forms.CharField(
        label='প্রতি একক মূল্য',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ১০০ বা 100',
            'autocomplete': 'off',
        })
    )

    stock_quantity = forms.CharField(
        label='স্টক পরিমাণ',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ৫০ বা 50',
            'autocomplete': 'off',
        })
    )

    image = forms.ImageField(
        label='পণ্য ছবি',
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = InventoryProduct
        fields = ['name', 'description', 'unit', 'price_per_unit', 'stock_quantity', 'is_active', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'পণ্যের নাম লিখুন'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'পণ্যের বিবরণ লিখুন'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_price_per_unit(self):
        price = self.cleaned_data.get('price_per_unit')
        if price:
            converted = bangla_to_english_number(str(price).strip())
            converted = converted.replace(',', '').replace(' ', '')
            try:
                return float(converted)
            except ValueError:
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন')
        return 0

    def clean_stock_quantity(self):
        quantity = self.cleaned_data.get('stock_quantity')
        if quantity:
            converted = bangla_to_english_number(str(quantity).strip())
            converted = converted.replace(',', '').replace(' ', '')
            try:
                return float(converted)
            except ValueError:
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন')
        return 0





class InvoiceForm(forms.ModelForm):
    """ইনভয়েস ফর্ম - প্রতিটি পণ্যে আলাদা ছাড় সহ (items JSON দিয়ে পরিচালিত)"""

    paid_amount = forms.CharField(
        label='পরিশোধিত টাকা',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ১০০০ বা 1000',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Invoice
        fields = ['customer_name', 'mobile_number', 'paid_amount', 'sale_date', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ক্রেতার নাম'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'মোবাইল নাম্বার'
            }),
            'sale_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'নোট লিখুন (ঐচ্ছিক)'
            }),
        }

    def clean_paid_amount(self):
        paid = self.cleaned_data.get('paid_amount')
        if paid:
            converted = bangla_to_english_number(str(paid).strip())
            converted = converted.replace(',', '').replace(' ', '')
            try:
                return float(converted)
            except ValueError:
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন')
        return 0


class PaymentForm(forms.ModelForm):
    """পেমেন্ট ফর্ম - আংশিক পেমেন্ট যোগ করার জন্য"""

    amount = forms.CharField(
        label='পেমেন্টের পরিমাণ',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ৫০০ বা 500',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'নোট (ঐচ্ছিক)'
            }),
        }

    def clean_amount(self):
        from decimal import Decimal
        amount = self.cleaned_data.get('amount')
        if amount:
            converted = bangla_to_english_number(str(amount).strip())
            converted = converted.replace(',', '').replace(' ', '')
            try:
                # CRITICAL FIX: Return Decimal, not float, to prevent precision loss
                value = Decimal(converted)
                if value <= 0:
                    raise forms.ValidationError('পেমেন্টের পরিমাণ ০ এর চেয়ে বেশি হতে হবে')
                return value
            except (ValueError, InvalidOperation):
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন')
        return Decimal('0')


class OrderPaymentForm(forms.ModelForm):
    """অর্ডার পেমেন্ট ফর্ম - কাস্টম অর্ডারের আংশিক পেমেন্ট"""

    amount = forms.CharField(
        label='পেমেন্টের পরিমাণ',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ৫০০ বা 500',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = OrderPayment
        fields = ['amount', 'payment_date', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'নোট (ঐচ্ছিক)'
            }),
        }

    def clean_amount(self):
        from decimal import Decimal
        amount = self.cleaned_data.get('amount')
        if amount:
            converted = bangla_to_english_number(str(amount).strip())
            converted = converted.replace(',', '').replace(' ', '')
            try:
                # CRITICAL FIX: Return Decimal, not float, to prevent precision loss when saving
                value = Decimal(converted)
                if value <= 0:
                    raise forms.ValidationError('পেমেন্টের পরিমাণ ০ এর চেয়ে বেশি হতে হবে')
                return value
            except (ValueError, InvalidOperation):
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন')
        return Decimal('0')
