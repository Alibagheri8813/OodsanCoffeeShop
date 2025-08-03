from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Comment, Order, OrderFeedback, UserProfile, UserAddress

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

class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'birth_date', 'avatar', 'bio']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تلفن خود را وارد کنید'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'درباره خود بنویسید...'
            })
        }

class UserAddressForm(forms.ModelForm):
    """Form for managing user addresses"""
    class Meta:
        model = UserAddress
        fields = ['title', 'full_address', 'city', 'state', 'is_default']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان آدرس (مثل خانه، محل کار)'
            }),
            'full_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'آدرس کامل خود را وارد کنید'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شهر'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'استان'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class CheckoutForm(forms.ModelForm):
    """Updated checkout form with address selection"""
    address = forms.ModelChoiceField(
        queryset=UserAddress.objects.none(),
        empty_label="آدرس مورد نظر را انتخاب کنید",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    postal_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'کد پستی را وارد کنید'
        })
    )
    
    class Meta:
        model = Order
        fields = ['delivery_method', 'notes']
        widgets = {
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیحات اضافی (اختیاری)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['address'].queryset = UserAddress.objects.filter(user=user)

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