from django import forms
from decimal import InvalidOperation
from .models import Order, InventoryProduct, Invoice, Payment, OrderPayment, OrderItem


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
    """অর্ডার ফর্ম - একাধিক পণ্য সাপোর্ট সহ"""

    # This field is not used directly - items are managed via JavaScript
    total_price = forms.CharField(
        label='মোট মূল্য',
        required=False,
        widget=forms.HiddenInput(),
    )

    cash_paid = forms.CharField(
        label='নগদ পরিশোধ',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ৫০০ বা 500',
            'autocomplete': 'off',
        })
    )

    # Hidden field to store items JSON
    items_json = forms.CharField(
        label='পণ্যসমূহ',
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Order
        fields = [
            'customer_name', 'mobile_number', 'cash_paid',
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

    def clean_cash_paid(self):
        """নগদ পরিশোধ ক্লিন করা - বাংলা সংখ্যা সাপোর্ট"""
        cash_paid = self.cleaned_data.get('cash_paid')
        if cash_paid:
            converted = bangla_to_english_number(str(cash_paid).strip())
            converted = converted.replace(',', '').replace(' ', '')
            try:
                return float(converted)
            except ValueError:
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন (উদাহরণ: ৫০০ বা 500)')
        return 0

    def clean_items_json(self):
        """Validate items JSON"""
        import json
        items_json = self.cleaned_data.get('items_json', '[]')
        try:
            items = json.loads(items_json)
        except json.JSONDecodeError:
            raise forms.ValidationError('অবৈধ পণ্য তথ্য')
        
        if not items:
            raise forms.ValidationError('কমপক্ষে একটি পণ্য যোগ করুন')
        
        return items

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Save order first to get PK
        if commit:
            instance.save()
            
            # Delete existing items if editing
            if instance.pk:
                instance.items.all().delete()
            
            # Create OrderItem records
            items_data = self.cleaned_data.get('items_json', [])
            from decimal import Decimal
            
            for item_data in items_data:
                OrderItem.objects.create(
                    order=instance,
                    product_name=item_data['product_name'],
                    product_description=item_data.get('product_description', ''),
                    quantity=Decimal(str(item_data['quantity'])),
                    unit_price=Decimal(str(item_data['unit_price'])),
                )
        
        return instance


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # Editing existing product
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['unit'].widget.attrs['disabled'] = True
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError('পণ্যের নাম আবশ্যক')
        return name.strip().title()
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        unit = cleaned_data.get('unit')
        
        # Check for duplicate products (only for new products)
        if name and unit and not self.instance.pk:
            if InventoryProduct.objects.filter(name__iexact=name, unit=unit).exists():
                raise forms.ValidationError(f'এই নামে এবং এককে একটি পণ্য ইতিমধ্যেই আছে: {name} ({dict(self.fields["unit"].choices)[unit]})')
        
        return cleaned_data

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

    global_discount = forms.CharField(
        label='মোট ডিসকাউন্ট (%)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ৫ বা 5',
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

    def clean_global_discount(self):
        """মোট ডিসকাউন্ট (%) ক্লিন করা - বাংলা সংখ্যা সাপোর্ট"""
        from decimal import Decimal

        value = self.cleaned_data.get('global_discount')
        if value in (None, ''):
            return Decimal('0')

        converted = bangla_to_english_number(str(value).strip())
        converted = converted.replace(',', '').replace(' ', '')
        try:
            disc = Decimal(converted)
        except (ValueError, InvalidOperation):
            raise forms.ValidationError('সঠিক সংখ্যা লিখুন')

        if disc < 0 or disc > 100:
            raise forms.ValidationError('ডিসকাউন্ট ০ থেকে ১০০ এর মধ্যে হতে হবে')

        return disc


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
        from decimal import Decimal, InvalidOperation
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


class StockManagementForm(forms.Form):
    """স্টক ব্যবস্থাপনা ফর্ম"""
    
    operation_type = forms.ChoiceField(
        label='অপারেশন',
        choices=[
            ('add', 'স্টক যোগ করুন'),
            ('remove', 'স্টক কমান'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'updateFormTitle()'
        })
    )
    
    quantity = forms.CharField(
        label='পরিমাণ',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control bangla-number-input',
            'placeholder': 'উদাহরণ: ১০ বা 10',
            'autocomplete': 'off',
        })
    )
    
    notes = forms.CharField(
        label='নোট',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'কারণ বা নোট লিখুন (ঐচ্ছিক)'
        })
    )
    
    def clean_quantity(self):
        from decimal import Decimal, InvalidOperation
        quantity = self.cleaned_data.get('quantity')
        if quantity:
            converted = bangla_to_english_number(str(quantity).strip())
            converted = converted.replace(',', '').replace(' ', '')
            try:
                value = Decimal(converted)
                if value <= 0:
                    raise forms.ValidationError('পরিমাণ ০ এর বেশি হতে হবে')
                return value
            except (ValueError, InvalidOperation):
                raise forms.ValidationError('সঠিক সংখ্যা লিখুন')
        return Decimal('0')