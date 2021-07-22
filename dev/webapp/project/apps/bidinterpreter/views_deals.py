from django.http import Http404
from django.contrib.auth.models import Group
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse

from .models import Deal, DealInvite

import logging
logger = logging.getLogger(__name__)


# Helper functions

def get_deal_id(post_request):
    filtered_fields = [(key, value) for key, value in post_request.items() if "filepond" in key]
    deal_id = False
    fieldname = False
    if len(filtered_fields) > 0:
        fieldname = filtered_fields[0][0]
        deal_id = filtered_fields[0][0].split("[")[1].replace("]", "")

    return fieldname, deal_id


class DealInviteDelete(DeleteView):
    model = DealInvite
    template_name = "bidinterpreter/bid_confirm_delete.html"
    success_url = False

    def dispatch(self, *args, **kwargs):
        self.success_url = reverse_lazy('bidinterpreter:deal-users', kwargs={'pk': self.kwargs['deal_id']})
        deal = Deal.objects.get(pk=self.kwargs['deal_id'])

        if deal.user and hasattr(deal.user, "id") and deal.user.id == self.request.user.id:
            deal_owner = True
        else:
            deal_owner = False

        if deal_owner:
            return super().dispatch(*args, **kwargs)

        raise Http404


class DealCreate(CreateView):
    model = Deal
    fields = ['deal_name']
    template_name = 'bidinterpreter/deal_form.html'

    def form_valid(self, form):
        # super(DealCreate, self).save(*args, **kwargs)
        deal = form.save()
        self.object = deal
        if self.request.user.is_authenticated:
            self.object.user = self.request.user
        group, created = Group.objects.get_or_create(name=f'deal_{deal.id}')
        group.user_set.add(self.request.user)
        return super(DealCreate, self).form_valid(form)


class DealUpdate(UpdateView):
    model = Deal
    fields = ['deal_name']
    template_name = 'bidinterpreter/deal_form.html'

    def dispatch(self, *args, **kwargs):
        deal = Deal.objects.get(pk=self.kwargs['pk'])

        if deal.user and hasattr(deal.user, "id") and deal.user.id == self.request.user.id:
            deal_owner = True
        else:
            deal_owner = False

        if deal_owner:
            return super().dispatch(*args, **kwargs)

        raise Http404


class DealDelete(DeleteView):
    model = Deal
    success_url = reverse_lazy('bidinterpreter:index')

    def dispatch(self, *args, **kwargs):
        deal = Deal.objects.get(pk=self.kwargs['pk'])

        if deal.user and hasattr(deal.user, "id") and deal.user.id == self.request.user.id:
            deal_owner = True
        else:
            deal_owner = False

        if deal_owner:
            return super().dispatch(*args, **kwargs)

        raise Http404

