from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Order, Comment

class UserRegistrationForm(UserCreationForm):
    """Beautiful user registration form with profile fields"""
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'شماره تلفن (اختیاری)'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'شهر'
        })
    )
    province = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'استان'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام کاربری'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ایمیل'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CheckoutForm(forms.Form):
    """Beautiful checkout form with delivery options"""
    DELIVERY_CHOICES = [
        ('pickup', 'دریافت حضوری'),
        ('post', 'ارسال پستی'),
    ]
    
    delivery_method = forms.ChoiceField(
        choices=DELIVERY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'delivery-option'}),
        initial='pickup',
        label='روش ارسال'
    )
    
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'آدرس کامل ارسال'
        }),
        required=False,
        label='آدرس ارسال'
    )
    
    postal_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'کد پستی'
        }),
        required=False,
        label='کد پستی'
    )
    
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'شماره تلفن'
        }),
        label='شماره تلفن'
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'توضیحات اضافی (اختیاری)'
        }),
        required=False,
        label='توضیحات'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        delivery_method = cleaned_data.get('delivery_method')
        shipping_address = cleaned_data.get('shipping_address')
        postal_code = cleaned_data.get('postal_code')
        
        if delivery_method == 'post':
            if not shipping_address:
                raise forms.ValidationError('برای ارسال پستی، آدرس ارسال الزامی است.')
            if not postal_code:
                raise forms.ValidationError('برای ارسال پستی، کد پستی الزامی است.')
        
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'city', 'province', 'postal_code', 'birth_date', 'profile_image']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تلفن'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'آدرس کامل'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شهر'
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'استان'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کد پستی'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }

class CommentForm(forms.ModelForm):
    """Product review form"""
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'نظر خود را بنویسید...'
            })
        }
        labels = {
            'text': 'نظر شما'
        }

class SearchForm(forms.Form):
    """Product search form"""
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'جستجو در محصولات...',
            'id': 'search-input'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="همه دسته‌بندی‌ها",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'حداقل قیمت'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'حداکثر قیمت'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('name', 'نام'),
            ('price_low', 'قیمت (کم به زیاد)'),
            ('price_high', 'قیمت (زیاد به کم)'),
            ('newest', 'جدیدترین'),
            ('popular', 'محبوب‌ترین')
        ],
        required=False,
        initial='name',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category
        self.fields['category'].queryset = Category.objects.all() 