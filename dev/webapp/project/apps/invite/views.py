from django.views.generic.detail import DetailView
from django.shortcuts import render, redirect


from project.apps.bidinterpreter.models import DealInvite, Deal

from datetime import datetime


class InviteView(DetailView):
    template_name = "invite/invite.html"
    model = DealInvite

    def get_object(self):
        print(self.request.user, self.kwargs.get('invite_code'))
        invite = DealInvite.objects.get(unique_id=self.kwargs.get('invite_code'))
        invite.viewed = datetime.now()

        try: 
            # User is not the same
            if self.request.user.id != invite.deal.user.id:
                invite.status = 0
            elif not self.request.get('user', {}).get('id', False):
                invite.status = 0
        except:
            pass 

        invite.save()
        return invite # or request.POST

    def get(self,request,*args,**kwargs):
        
        if self.request.GET.get('accept', False):
            self.request.session['invite'] = self.kwargs.get('invite_code')
            response = redirect('/accounts/google/login/?action=reauthenticate&process=login&next=%2Fbidinterpreter/%3Finvite=' + self.kwargs.get('invite_code'))
            response.set_cookie('invite', self.kwargs.get('invite_code'))
            return response

        return super().get(request,*args,**kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # deal = Deal.objects.get(id=self.object.deal.id)
        print(vars(context['object']), self.object.deal.deal_name)

        return context

