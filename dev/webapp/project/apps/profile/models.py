from django.db import models
from django.urls import reverse
from datetime import datetime
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField

class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Other fields here
    first_name = models.CharField(max_length=75)
    last_name = models.CharField(max_length=75)
    company = models.CharField(max_length=75)
    phone = PhoneNumberField()
    email = models.EmailField(verbose_name= _('Personal Email'))
    accepted_eula = models.BooleanField(verbose_name= _('Accept EULA'), default=False)
    
    # def get_absolute_url(self): # new
    #     return reverse('profile:update_profile')

    class Meta:
        permissions = (
            ('profile_complete', 'Completed profile after registration.'),
        )
