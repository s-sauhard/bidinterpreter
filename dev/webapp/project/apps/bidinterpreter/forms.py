from django.db import models
from django import forms
from django.contrib.auth.models import User
from .models import Bid, BidDoc

class BidForm(forms.ModelForm):

    # deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    # date_uploaded = models.DateTimeField(auto_now_add=True, blank=True)
    # date_received = models.DateTimeField(default= datetime.now, blank=True)
    # bidder = models.CharField(max_length=250, blank=True)
    # purchase_price = models.IntegerField(default=0)
    # due_diligence = models.CharField(max_length=250, blank=True)
    # closing = models.CharField(max_length=250, blank=True)
    # comments = models.CharField(max_length =1000, blank=True)
    # deposit = models.CharField(max_length=250, blank=True)
    # status = models.IntegerField(default=0) # 0 = unknown 1 = manual entry, 2 = written bid, guess 3 = written bid, confirmed
    # def __init__(self, *args, **kw):
    #     super(BidForm, self).__init__(*args, **kw)
    #     self.fields.keyOrder = [
    #         'deal',
    #         'bid_doc',
    #         'purchase_price',
    #         'deposit',
    #         'due_diligence',
    #         'closing',
    #         'comments',
    #         'active'
    #     ]

    class Meta:
        model = Bid
        fields = [
            # bidder, price, deposit, due diligence, closing, comments
            'deal',
            'bid_doc',
            'company_name',
            'purchase_price',
            'deposit',
            'due_diligence',
            'closing',
            'comments',
            'active'
        ]
        widgets = {
            'deal':     forms.HiddenInput(),
            'bid_doc':  forms.HiddenInput(),
            'bidder':   forms.HiddenInput(),
            'bid_doc_id': forms.HiddenInput(),
            'comments': forms.Textarea()
        }
        help_texts = {
            'active': "Make your bid active once you're ready to share it with the deal owner.",
        }


class BidDocForm(forms.ModelForm):
    class Meta:
        model = BidDoc
        fields = '__all__'


## Bid wizard test
class FormStepOne(forms.Form):
    name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    phone = forms. CharField(max_length=100)
    email = forms.EmailField()


class FormStepTwo(forms.Form):
    job = forms.CharField(max_length=100)
    salary = forms.CharField(max_length=100)
    job_description = forms.CharField(widget=forms.Textarea)