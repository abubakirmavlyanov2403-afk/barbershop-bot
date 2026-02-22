from django import forms
from allauth.account.forms import SignupForm
from .models import User

class CustomSignupForm(SignupForm):
    phone = forms.CharField(
        max_length=12,
        min_length=12,
        required=True,
        label='Телефон',
        widget=forms.TextInput(attrs={'placeholder': '+7XXXXXXXXXX', 'class': 'form-control'})
    )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not phone.startswith('+'):
            if phone.startswith('7'):
                phone = '+' + phone
            elif phone.startswith('8'):
                phone = '+7' + phone[1:]
            else:
                phone = '+7' + phone
        import re
        phone = re.sub(r'[^\d+]', '', phone)
        if not phone.startswith('+7') or len(phone) != 12:
            raise forms.ValidationError("Телефон должен быть в формате +7XXXXXXXXXX (10 цифр после +7)")
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Этот телефон уже зарегистрирован")
        return phone

    def save(self, request):
        user = super().save(request)
        user.phone = self.cleaned_data['phone']
        user.save()
        return user