from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        if 'phone' in form.cleaned_data:
            user.phone = form.cleaned_data['phone']
        if commit:
            user.save()
        return user