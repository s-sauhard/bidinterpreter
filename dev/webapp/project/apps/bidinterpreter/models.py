from django.db import models
from django.urls import reverse
from datetime import datetime
from django.conf import settings
from django.utils import timezone


class Deal(models.Model):
    deal_name = models.CharField(max_length=250, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('bidinterpreter:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.deal_name


class DealInvite(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    email = models.EmailField(unique=False, max_length=254)
    unique_id = models.CharField(max_length=100, null=True)
    status = models.IntegerField(default=-1, blank=True)  # -1 = unprocessed, 0 = invite viewed, 1 = invite used
    user_group = models.CharField(max_length=255, blank=True)
    user_permission = models.IntegerField(default=0)  # 0 = view_only, 1 = can_bid
    viewed = models.DateTimeField(auto_now_add=False, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('deal', 'email',)


class BidDoc(models.Model):
    # bid = models.ForeignKey(Deal, on_delete=models.CASCADE)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    status = models.IntegerField(default=0, blank=True)  # 0 = unprocessed, 1 = in-progress, 2 = ready
    doc_type = models.IntegerField(default=0)  # 0 = not bid, 1 = bid, 2 = bid image
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    text = models.TextField(blank=True)
    word_coords = models.JSONField(blank=True, null=True)
    original_doc_name = models.CharField(max_length=250, blank=False)
    created = models.DateTimeField(auto_now_add=True)


class BidDocStats(models.Model):
    biddoc = models.ForeignKey(BidDoc, on_delete=models.CASCADE, null=True)
    original_doc_name = models.CharField(max_length=250, blank=False)  # A bit redunant but this is for anlaytics
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(auto_now_add=False, null=True)
    results = models.JSONField(blank=True, null=True)


class Bid(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    bid_doc = models.ForeignKey(BidDoc, on_delete=models.CASCADE, null=True, blank=True)
    company_name = models.CharField(max_length=250, blank=True)
    date_uploaded = models.DateTimeField(auto_now_add=True, blank=True)
    date_received = models.DateTimeField(auto_now_add=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    purchase_price = models.DecimalField(max_digits=25, decimal_places=2)
    due_diligence = models.CharField(max_length=250, blank=True)
    closing = models.CharField(max_length=250, blank=True)
    comments = models.CharField(max_length=1000, blank=True)
    deposit = models.CharField(max_length=250, blank=True)
    active = models.BooleanField(default=False)
    status = models.IntegerField(
        default=0)  # 0 = unknown 1 = manual entry, 2 = written bid, guess 3 = written bid, confirmed

    def __str__(self):
        return str(self.user) + '-' + str(self.date_received)

# class BidDealDoc(models.Model):
#     bid_id= models.ForeignKey(Bid, on_delete=models.CASCADE)
#     dealdoc_id = models.ForeignKey(DealDoc, on_delete=models.CASCADE)
#     created = models.DateTimeField(auto_now_add=True)
