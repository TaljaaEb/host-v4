from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Order


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Password'
    }))


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address',
                  'postal_code', 'city']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control',
                                                  'placeholder': 'John'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control',
                                                 'placeholder': 'Doe'}),
            'email': forms.EmailInput(attrs={'class': 'form-control',
                                              'placeholder': 'john@example.com'}),
            'address': forms.TextInput(attrs={'class': 'form-control',
                                               'placeholder': '123 Main St'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control',
                                                   'placeholder': '12345'}),
            'city': forms.TextInput(attrs={'class': 'form-control',
                                            'placeholder': 'New York'}),
        }


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1, max_value=99,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'value': 1, 'min': 1
        })
    )
    override = forms.BooleanField(
        required=False, initial=False,
        widget=forms.HiddenInput
    )
