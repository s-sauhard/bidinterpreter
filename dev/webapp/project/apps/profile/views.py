import os
from .models import UserProfile
from django.http.response import HttpResponse, HttpResponseNotFound, HttpResponseServerError, HttpResponseRedirect, JsonResponse
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView
from django.urls import reverse_lazy, reverse
from django import forms
from django.contrib import messages
from allauth.socialaccount.models import SocialAccount
from django.utils.html import format_html
import logging

from .forms import SignupForm
from project.apps.bidinterpreter.models import DealInvite, Deal

# UserProfile
app_name = "profile"

class CreateUserProfileView(generic.CreateView):
    model = UserProfile
    form_class = SignupForm
    # fields = "__all__"
    template_name = 'profile/userprofile_form.html'
    success_url = "/bidinterpreter"

    def get_initial(self):
        print("get initial:", self.request.user)
        print("session is:", self.request.session.session_key, self.request.session.get('invite', False))

        # Set session if found from cookie.
        invite_cookie = self.request.COOKIES.get('invite', False)
        print("Cookies are:", self.request.COOKIES)
        if invite_cookie:
            self.request.session['invite'] = invite_cookie

        social_info = self.request.user.socialaccount_set.all().values().first() # Finally found the gold!
        logging.root.setLevel(logging.NOTSET)
        logger = logging.getLogger(__name__)
        logger.debug(social_info.keys())
        print("given", social_info.keys())

        initial = {
            'user': self.request.user,
            'first_name': social_info.get('extra_data', {}).get('given_name'), ## Attempts to get nested result, but returns blank if none found
            'last_name':  social_info.get('extra_data', {}).get('family_name'),
            'email':      social_info.get('extra_data', {}).get('email'),
            'invite':     self.request.session.get('invite', False)
        }
        return initial

    # def get(self, request, *args, **kwargs):
    #     form = self.form_class()
    #     print("form is:", )
    #     # form.fields['offered_player'].queryset = petitioner.players
    #     return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        
        # Add user permissions "complete_profile"
        ## Useful for checking which permissions exist
        # debug = Permission.objects.all()
        # for row in debug.values():
        #     print(row)

        result = form.save(commit = False)
        result.user_id = self.request.user.pk
        permission = Permission.objects.get(codename='profile_complete')
        self.request.user.user_permissions.add(permission)
        
        self.object = result
        self.object.save()

        ## Session check for invite redirect
        unique_id =  self.request.session.get('invite', False)
        if unique_id: # If user has a session from an invite 
            # user_group_map = {
            #     "0": f"group_{self.kwargs.get('pk')}_view_only",
            #     "1": f"group_{self.kwargs.get('pk')}_can_bid"
            # }
            invite = DealInvite.objects.get(unique_id = unique_id)
            group_name = invite.user_group
            print('adding user to group', group_name)
            group, created = Group.objects.get_or_create(name=group_name)
            group.user_set.add(self.request.user)
        else:
            print('Session invite not set!')

        # UserProfile.objectes.create()
        print("Saved form result:", result, "errors:", form.errors, "Non-field errors:", form.non_field_errors)

        # do something with self.object
        # remember the import: 
        message = message = format_html('Profile created successfully. <a href="{}">View current deals</a>?', reverse('bidinterpreter:index'))
        messages.success(self.request, message)

        return super(CreateUserProfileView, self).form_valid(form)
        # return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.has_perm('profile.profile_complete'):
            context['profile_complete'] = True
        else:
            print("doesn't have permission")
            context['profile_complete'] = False

        ## Session check for invite redirect
        unique_id =  self.request.session.get('invite', False)
        if unique_id: # If user has a session from an invite 
            invite = DealInvite.objects.get(unique_id = unique_id)
            context['invite'] = invite
        else:
            context['invite'] = False
        return context

class UpdateUserProfileView(generic.UpdateView):
    model = UserProfile
    fields = "__all__"
    template_name = 'profile/userprofile_form.html'

    def get_object(self):
        print(self.request.user, self.request.user.pk, UserProfile.objects.all())

        obj, _ = UserProfile.objects.get_or_create(user_id=self.request.user.pk) # or request.POST

        return obj

    def get_context_data(self, **kwargs):
        print("kwargs:", kwargs)
        context = super().get_context_data(**kwargs)
        print("context is:", context)
        if self.request.user.has_perm('profile.profile_complete'):
            context['profile_complete'] = True
        else:
            print("doesn't have permission")
            context['profile_complete'] = False
        return context

    def get_initial(self):
        print("get initial:", self.kwargs.get('user'))
        initial = {
            'user': self.request.user,
        }
        return initial
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully')
        return self.render_to_response(self.get_context_data())
