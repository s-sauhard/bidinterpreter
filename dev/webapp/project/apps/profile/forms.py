from . import models

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm, SetPasswordField, PasswordField, LoginForm
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget, PhoneNumberPrefixWidget
from django.utils.safestring import mark_safe


class SignupForm(forms.ModelForm):
    """SignForm docstring."""

    first_name  = forms.CharField(
        max_length = 75,
    )
    last_name   = forms.CharField(
        max_length = 75,
    )
    company     = forms.CharField(
        max_length = 75,
    )
    phone       = PhoneNumberField(
        widget = PhoneNumberInternationalFallbackWidget(
            attrs = {'placeholder': 'ie: +14151234567'}
        )
    )
    email = forms.EmailField(
        # options here..
    )
    accepted_eula = forms.BooleanField(
        label = mark_safe("By clicking submit you agree to our <a href='#'>Privacy Policy</a> and <a href='#'>Terms and Conditions</a>."), 
        required = True, 
        error_messages = {
            "required": "You must accept our terms and conditions to use our platform."
        }
    )

    # def myclean():
    #     _

    # def signup(self, request, user):
    #     user.first_name = self.cleaned_data['first_name']
    #     user.last_name = self.cleaned_data['last_name']
    #     user.save()
    #     return user

    def __init__(self, *args, **kwargs):

        obj = super(SignupForm, self).__init__(*args, **kwargs)

        self.request = kwargs.pop('request', None)
        print("kwargs ARE:", kwargs)
        if kwargs['initial']['invite']:
            print("fields", self.fields)
            self.fields['email'].disabled = True

        return obj

    def save(self, *args, **kwargs): # Fixes "NOT NULL constraint failed: profile_userprofile.user_id" to user form element when not displayed
        kwargs['commit'] = False
        obj = super(SignupForm, self).save(*args, **kwargs)
        if self.request:
            obj.user = self.request.user
            obj.save()
        return obj

    class Meta:
        model = models.UserProfile
        fields = [
            'first_name',
            'last_name',
            'company',
            'phone',
            'email'
        ]


