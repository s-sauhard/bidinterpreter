import time, os
from .models import Deal, DealInvite, Bid, BidDoc, BidDocStats
from django.http.response import HttpResponse, HttpResponseServerError,JsonResponse
from django.utils.safestring import mark_safe

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseNotFound, Http404

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User

from django.conf import settings
from django.shortcuts import redirect
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from django_tables2 import tables, SingleTableView

from django.core.mail import send_mail
from django.db import IntegrityError

# Handling file uplaods with rest_framework 
from rest_framework.parsers import MultiPartParser

from rest_framework.views import APIView

from datetime import datetime
from .forms import BidForm, BidDocForm
from .tables import BidTable, DealUserTable, DealInviteTable

# additional libraries
import json, uuid, re

# Checking email is completely valid
from validate_email import validate_email

# File validation
import magic

# Kafka replacement -- background processing
from background_task import background

## For azure extracts
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes

## New Azure / OCR / ML Service Library
from .ocr_matching import AzureVisionService, EntityRegexMatch

## Prototype extract data and coordinates
from .doctools import DocTools

## PDF Annotate
from pdf_annotate import PdfAnnotator, Location, Appearance

import logging, decimal
logger = logging.getLogger(__name__)

class NotFoundView(TemplateView):
    template_name = "global/404.html"

class IndexView(LoginRequiredMixin, generic.ListView):
    login_url = "/accounts/login"
    template_name = 'bidinterpreter/index_bb.html'
    context_object_name = 'all_deals'

    def dispatch(self, *args, **kwargs):
        """ dispatch handles the request initially.
        
        We'll use this method to handle permissions checking.  Perhaps we can create a decorator for this later.

        Returns:
            [type]: [description]
        """
        if not self.request.user.has_perm('profile.profile_complete'):
            print("redirecting to create profile")
            return redirect('profile:create_profile')

        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        query_term = self.request.GET.get('q',False)
        if query_term:
            results = Deal.objects.filter(deal_name__icontains=query_term)
            # if results.count()==1:
            #     print(results[0].pk)
            #     return reverse('bidinterpreter:detail', kwargs = {'pk':results[0].pk})
        else:
            results = Deal.objects.all().order_by('-deal_name')
        return self.filter_by_group_permission(results, self.request.user)
    # def get(self,request,*args,**kwargs):
    #     print("get")
    #     return self.get(request,*args,**kwargs)

    def filter_by_group_permission(self, queryset, user):
        """filter_by_group_permission

        This method will filter groups based on if users are either #1 associated with a f"group_[id]_view_only" or "*_can_bid" 
        or #2 they own the deal itself.

        In hindsight, this method can be improved by finding user groups, pulling the id's out of them, then filtering prior 
        to querying all deals rather than querying all deals then post-filtering.  This should be re-written prior to scaling.

        Args:
            queryset ([type]): [description]
            user ([type]): [description]

        Returns:
            [type]: [description]
        """

        user_groups = set(self.request.user.groups.values_list('name', flat = True))
        exclude_group_ids = []
        print("user groups:", user_groups)
        for row in queryset:
            group_id = row.id
            user     = row.user

            # Check if deal has a user
            if user and hasattr(user, "id"):
                user_id = row.user.id 
            else:
                user_id = False

            # qualified groups
            groups = set([f"group_{row.id}_view_only", f"group_{row.id}_can_bid"])
            group_intersection = user_groups.intersection(groups)

            if group_intersection == set() and user_id != self.request.user.id:
                exclude_group_ids.append(group_id)

        return Deal.objects.exclude(id__in =exclude_group_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q']= self.request.GET.get('q', False)
       
        return context


# def detail(request, id):
    #deal = Deal.objects.filter(pk=id)
    #deal = get_object_or_404(Deal, pk=id)
    # return render(request, 'bidinterpreter/detail.html', {'deal': deal})



class DetailView(SingleTableView):
    """DetailView

    Url:
        url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    Args:
        SingleTableView ([type]): [description]
    """
    model = Bid
    template_name = 'bidinterpreter/detail.html'
    table_class = BidTable
    raw_sql = """
        SELECT * FROM 
        (
            SELECT
                b.id,
                d.id AS doc_id,
                d.deal_id,
                d.user_id,
                d.status AS doc_status,
                b.status AS bid_status,
                d.original_doc_name,
                b.purchase_price,
                b.due_diligence,
                b.closing,
				CASE b.date_uploaded 
					WHEN NULL THEN d.created
					ELSE d.created
				END	AS created
                
            FROM bidinterpreter_biddoc d 
            LEFT JOIN bidinterpreter_bid b ON b.bid_doc_id = d.id 
            UNION	
            SELECT 
                b.id,
                b.bid_doc_id AS doc_id,
                b.deal_id,
                b.user_id,
                b.status AS doc_status,
                b.status AS bid_status,
                d.original_doc_name,
                b.purchase_price,
                b.due_diligence,
                b.closing,
				CASE b.date_uploaded 
					WHEN NULL THEN d.created
					ELSE b.date_uploaded
				END AS created
            FROM bidinterpreter_bid b
            LEFT JOIN bidinterpreter_biddoc d ON d.id = b.bid_doc_id 
        ) doc
        WHERE doc.deal_id = {deal_id}
        ORDER BY (
			CASE doc_status
			WHEN 1 THEN 0
			WHEN 2 then 1
			WHEN 3 then 2
			WHEN 0 then 3
			END
		) ASC
    """

    def get_queryset(self, **kwargs):

        #bidset = Bid.objects.filter(deal=self.kwargs.get('pk')) # raw('SELECT bidinterpreter_bid.*, bidinterpreter_biddoc.* FROM bidinterpreter_bid LEFT JOIN bidinterpreter_biddoc ON bidinterpreter_bid.id = bidinterpreter_biddoc.bid_id WHERE deal_id='+self.kwargs.get('pk'))
            #.filter(deal=self.kwargs.get('pk'))
        # bidx = Bid.objects.prefetch_related('bid_set').get(deal='14')

       # qset = BidDoc.objects.select_related('bid').all()
            #filter(bid_deal=self.kwargs.get('pk'))
        bids = Bid.objects.raw(self.raw_sql.format(deal_id = self.kwargs.get('pk')))
        return bids
    #    # a1 = Bid.objects.filter(Bid__deal=self.kwargs.get('pk'))


    #     # return Bid.objects.filter(BidDoc__deal=self.kwargs.get('pk'))
    #     # return Bid.objects.filter(deal_id=self.kwargs.get('pk'))
    #     # .order_by('-pub_date')[:5]
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        ## TBD:  add count of items


        deal                    = Deal.objects.get(pk = self.kwargs.get('pk'))
        bids                    = self.get_queryset()
        context['deal']         = self.kwargs.get('pk')
        context['deal_name']    = deal
        context['table']        = BidTable(list(bids))
        context['bid_count']    = len(list(bids))
        context['owner_meta']   = deal.user
        
        #deal = Deal.objects.get(pk = context['deal'])

        print("deal user", deal.user)

        if deal.user and hasattr(deal.user, "id") and deal.user.id == self.request.user.id:
            context['deal_owner'] = True
        else:
            context['deal_owner'] = False

        # User count for subnav
        users_can_bid   = User.objects.filter(groups__name = f"group_{context['deal']}_can_bid")
        users_view_only = User.objects.filter(groups__name = f"group_{context['deal']}_view_only")

        context['bid_users']  = users_can_bid
        context['view_users'] = users_view_only 

        print('can bid users', users_can_bid)

        user_can_bid_ids    = [user.pk for user in users_can_bid]
        users_view_only_ids = [user.pk for user in users_view_only]

        context['user_count']   = users_can_bid.count() + users_view_only.count()

        if self.request.user.id in user_can_bid_ids:
            context['can_bid'] = True 

        if self.request.user.id in users_view_only_ids:
            context['view_only'] = True 

        # context['docs'] = BidDoc.objects.filter(deal = context['deal']) 
        # context['docs'] = BidDoc.objects.filter(bid_id=context['bid'])
        return context

class DealInviteDelete(DeleteView):

    model = DealInvite
    template_name = "bidinterpreter/bid_confirm_delete.html"
    success_url = False

    def dispatch(self, *args, **kwargs):
        self.success_url = reverse_lazy('bidinterpreter:deal-users', kwargs={'pk': self.kwargs['deal_id']})
        deal = Deal.objects.get(pk = self.kwargs['deal_id'])

        if deal.user and hasattr(deal.user, "id") and deal.user.id == self.request.user.id:
            deal_owner = True
        else:
            deal_owner = False

        if deal_owner:
            return super().dispatch(*args, **kwargs)
      
        raise Http404

class UserListView(SingleTableView):
    """UserLIstView

        Used for adding / removing users /w permissions for deals.  Labled "User Management" from the deal landing / bid summary page.

    Url:
        url(r'^(?P<pk>[0-9]+)/users$', views.UserListView.as_view(), name='deal-users'),

    Args:
        SingleTableView ([type]): [description]

    Returns:
        [type]: [description]
    """
    model = Deal
    template_name = 'bidinterpreter/users.html'
    table_class = BidTable

    def get_user_count(self, deal_id):
        users = User.objects.filter(groups__name=f'deal_{deal_id}')
        print(f"Users for deal_{deal_id}", users, users.count())
        return users.count()

    def add_user_group(self, request, json_data, *args, **kwargs):
        """add_user_to_group

            Refactored how permissions work and this method assumed only a single user group for deals.
            We are now using multiple groups for a single deal rather than individual permissions per user for scalability.
            In hindsight I would have used this single method to handle add and update -- will refactor given more time in the future.

        Args:
            request ([type]): [description]
            json_data ([type]): [description]

        Returns:
            [type]: [description]
        """

        action = json_data.get('action', False)
        user_type = json_data.get('user_type', False)

        user_group_map = {
            "0": f"group_{self.kwargs.get('pk')}_view_only",
            "1": f"group_{self.kwargs.get('pk')}_can_bid"
        }
        print("Action is:", action, "user type is:", user_type)
        if action and action == "add_user":
            
            group_name = user_group_map[user_type]
        else:
            return {
                "message":  "Could not add user.  Sorry about that.  Please try again later.",
                "error": True
            }

        # Add gro
        group, created = Group.objects.get_or_create(name=group_name)

        ### add user to group
        try:
            user = User.objects.get(username = json_data.get('username'))
        except ObjectDoesNotExist:
            user = False 

        response = dict()

        if user != False:       
            result = group.user_set.add(user)
            response['error']   = False
            response['message'] = 'User added successfully.'
        else:
            response['message'] = 'User does not exist.'
            response['error']   = True
        
        return response

    def remove_user_from_group(self, request, json_data = dict(), *args, **kwargs):

        groups = [
            f"group_{self.kwargs.get('pk')}_view_only",
            f"group_{self.kwargs.get('pk')}_can_bid",
            f"group_{self.kwargs.get('pk')}",           # Legacy group.  Leaving here to clean up any old data.
        ]

        for group_name in groups:

            group, created = Group.objects.get_or_create(name=group_name)
            user_ids = json_data.get('users', False)
            
            # Remove users from group
            if user_ids:
                users = [ User.objects.get(id = id) for id in user_ids]
                for user in users:
                    # Potentially may need to error check this
                    result = group.user_set.remove(user)
                
        return dict(message = "Removed user from all deal groups.")

    def add_user_group_view_only(self, request, json_data = dict(), *args, **kwargs):
        """add_user_group_view_only()

        Adds user to group_[id]_view_only.  Bit of a code reduancy because its the same exact function as add_user_group_can_bid.

        Returns:
            dict: Message that will be JSON encoded later.
        """
        group_name      = f"group_{self.kwargs.get('pk')}_view_only"
        group, created  = Group.objects.get_or_create(name=f"group_{self.kwargs.get('pk')}")

        ### add user to group
        try:
            user = User.objects.get(username = json_data.get('username'))
        except ObjectDoesNotExist:
            user = False 

        response = dict() 

        if user != False:       
            result = group.user_set.add(user)
            print("add_user_group_view_only Result: ", result)
            response['error']   = False
            response['message'] = 'User added to "view only" group successfully.'
        else:
            response['message'] = 'User does not exist.'
            response['error']   = True
        
        return response
        

    def update_user_groups(self, request, json_data = dict(), *args, **kwargs):
        action = json_data.get('action', False)
        users  = json_data.get('users', False)
        groups = [
            f"group_{self.kwargs.get('pk')}_view_only",
            f"group_{self.kwargs.get('pk')}_can_bid",
            f"group_{self.kwargs.get('pk')}",           # Legacy group.  Leaving here to clean up any old data.
        ]
        if action and users:

            for user_id in users:
               

                # Remove users from all groups first
                for group_name in groups:
                    print("removing ", user_id, "from", group_name)
                    group, created  = Group.objects.get_or_create(name=group_name)
                    user = User.objects.get(id = user_id) 
                    result = group.user_set.remove(user)

                # Add user to appropriate group based on action event type
                if action == "update_view":
                   
                    group, created  = Group.objects.get_or_create(name=groups[0])
                    user = User.objects.get(id = user_id) 
                    
                    result = group.user_set.add(user)
                    print("Adding user", user_id, "with user obj", user, "to group", groups[0], "result:", result)
                else:
                    group, created  = Group.objects.get_or_create(name=groups[1])
                    user = User.objects.get(id = user_id) 
                    result = group.user_set.add(user)
                    print("Adding user", user_id, "with user obj", user, "to group", groups[1], "result:", result)

        response = dict(message = "Operation completed", error = False) # TBD will have to add more descrie response and conditions
        return response
    
    def add_user_group_can_bid(self, request, json_data = dict(), *args, **kwargs):
        """add_user_group_can_bid()

        Adds user to group_[id]_view_only.  Bit of a code reduancy because its the same exact function as add_user_group_view_only.

        Returns:
            dict: Message that will be JSON encoded later.
        """
        group_name      = f"group_{self.kwargs.get('pk')}_can_bid"
        group, created  = Group.objects.get_or_create(name=f"group_{self.kwargs.get('pk')}")

        print('Group:', group)

        ### add user to group
        try:
            user = User.objects.get(username = json_data.get('username'))
        except ObjectDoesNotExist:
            print("count't find user", json_data.get('username'))
            user = False 

        response = dict()

        if user != False:       
            result = group.user_set.add(user)
            print("add_user_group_can_bid Result: ", result)
            response['error']   = False
            response['message'] = 'User added to "can bid" group successfully.'
        else:
            response['message'] = 'User does not exist.'
            response['error']   = True
        
        return response

    def send_invite_email(self, to, deal_name, unique_id):

        # user = User.objects.get(id=self.kwargs.get('pk'))
        subject = f"{self.request.user.get_full_name()} invited you to bid on {deal_name} @ loihub.com!"
        # print("user is:", user)
        message = f"[Placeholder text that explains 1) What we do, 2) What is being asked, 3) How safe it is to user our platform.] \n\nRegistration link: http://staging.loihub.com:8002/invite/{unique_id}"

        return send_mail(
            subject, 
            message, 
            settings.EMAIL_HOST_USER, 
            [to], 
            fail_silently = False
        )       

    def external_invite(self, request, json_data = dict(), *args, **kwargs):
        action = json_data.get('action', False)
        user_type = json_data.get('user_type', False)

        ## Check if email is even valid
        is_valid = validate_email(json_data.get('email', False), check_mx = False)
        if not is_valid:
            return dict(
                error   = True,
                message = "Email address is invalid."
            )

        user_group_map = {
            "0": f"group_{self.kwargs.get('pk')}_view_only",
            "1": f"group_{self.kwargs.get('pk')}_can_bid"
        }

        deal     = Deal.objects.get(id=self.kwargs.get('pk'))

        ## Check if user isn't deal owner already
        if json_data.get('email', False) == self.request.user.email:
            return dict(
                error   = True,
                message = "You can't invite yourself to your own deal."
            )

        ## first check if there's already a user with that email and if so, add them to the deal groups
        try:
            invited_user = User.objects.get(email = json_data.get('email', False))
            print("Invited exists in system is:", invited_user)

            ## Add to deal if exists
            group_name = user_group_map[user_type]
            group, created  = Group.objects.get_or_create(name=group_name)

            ### add user to group
            response = dict()
            print("result of adding user", invited_user, "to group", group)

            if invited_user != False:       
                result = group.user_set.add(invited_user)
                print('Result of adding user to deal:', result)
                return dict(
                    error   = False,
                    message = f'User with email has an account.  Added <strong>{invited_user.username}</strong> - <em>{invited_user.email}</em> to deal.'
                )
            else:
                return dict(
                    error   = True,
                    message = "User has LOIHub account but there was an error adding them to this deal."
                )

        except User.DoesNotExist:
            print("User does not exist:", json_data.get('email', False))

        data = dict(
            deal            = deal,
            email           = json_data.get('email', False),
            unique_id       = str(uuid.uuid4()),
            # status          = models.IntegerField(default = -1, blank = True) # -1 = unprocessed, 0 = invite viewed, 1 = invite used
            user_group      = user_group_map[user_type],
            user_permission = user_type # 0 = view_only, 1 = can_bid
        )

        print("data is:", data)
        
            # return {
            #     "message":  "Could not add user.  Sorry about that.  Please try again later.",
            #     "error": True
            # }

        # Add invite
        try:
            invite, created = DealInvite.objects.get_or_create(**data)
            error     = False
            is_unique = True
        except IntegrityError as e: 
            error = invite = created = False
            if any("UNIQUE constraint" in msg for msg in e.args):
                print("Couldn't create invite because ", e.args)
                is_unique = False

        response = dict()

        if created:
            # Send invite email
            result = self.send_invite_email(json_data.get('email', False), deal.deal_name, data['unique_id'])
            print("result of mail_send:", result)
            response['error']   = False
            response['message'] = 'Invite successfully sent.'
        elif not is_unique:       
            response['error']   = False
            response['message'] = 'Email address already invited to this deal.'
        else:
            response['message'] = f"Couldn't send invite. {{invite}}"
            response['error']   = True

        return response

    def post(self, request, *args, **kwargs): 
        
        # TBD:  check if user has permissions
        
        # Load JSON data from request
        json_data = json.loads(request.body)
        
        action = json_data.get('action', False)
        print("action is:", action)
        switch = {
            "remove":          self.remove_user_from_group,
            "update_bid":      self.update_user_groups,
            "update_view":     self.update_user_groups,
            "add_user":        self.add_user_group,
            "external_invite": self.external_invite
        }

        if not action:
            response = {
                "Message":  "Not a valid actions",
                "error":    True
            }

        response = switch[action](request, json_data, *args, **kwargs)

        # if json_data.get('action', False) == "remove":
        #     print("remove user action")
        #     response = self.remove_user_from_group(request, json_data, *args, **kwargs)
        # else:
        #     response = self.add_user_to_group(request, json_data, *args, **kwargs)

        return JsonResponse(response, safe=False)


    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        ## TBD:  add count of items
        context['deal']         = self.kwargs.get('pk')
        context['deal_name']    = Deal.objects.get(id=context['deal'])

        group_view_only = Group.objects.get_or_create(name=f"deal_{context['deal']}_view_only")
        group_can_bid   = Group.objects.get_or_create(name=f"deal_{context['deal']}_can_bid")

        
        # Bid count - TBD: limit to only 
        bids = Bid.objects.filter(deal_id = context['deal'])
        context['bid_count'] = bids.count()

        # User count for subnav
        from django.db.models import F
        from django.db.models import CharField, Value

        users_can_bid   = User.objects.filter(groups__name = f"group_{context['deal']}_can_bid").annotate(
            deal_id = Value(self.kwargs.get('pk'), CharField())
        )
        users_view_only = User.objects.filter(groups__name = f"group_{context['deal']}_view_only").annotate(
            deal_id = Value(self.kwargs.get('pk'), CharField())
        )

        context['user_count']   = users_can_bid.count() + users_view_only.count()

        if context['user_count']:
            context['group_users'] = True 
        else:
            context['group_users'] = False

        # DealUserTable

        print("------------------------------ data -----------------", list(users_can_bid))
        context['table'] = DealUserTable(list(users_can_bid) + list(users_view_only))

        deal = Deal.objects.get(pk = context['deal'])

        if deal.user and hasattr(deal.user, "id") and deal.user.id == self.request.user.id:
            context['deal_owner'] = True
        else:
            context['deal_owner'] = False

        # Get Bid count - TBD

        #print("Group is:", group, group.name)
        print("Users in group:", context['table']) 

        # for row in User.objects.filter(groups__name = "group_61"):
        #     print(dir(row))
        # user.user_set.add(your_user)

        invites      = DealInvite.objects.filter(deal = deal)
        print("Invites are:", invites.values())
        context['invite_table'] = DealInviteTable(list(invites))
        context['has_invites'] = True if(len(invites)) else False
        # RequestConfig(self.request).configure(context['invite_table'])

        print("Invite table:", invites, context['invite_table'])

        return context


def get_deal_id(post_request):
    filtered_fields = [(key, value) for key, value in post_request.items() if "filepond" in key]
    deal_id=False
    fieldname=False
    if len(filtered_fields) > 0:
        fieldname = filtered_fields[0][0]
        deal_id = filtered_fields[0][0].split("[")[1].replace("]", "")

    return fieldname, deal_id


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return list(str(o) for o in [o])
        return super(DecimalEncoder, self).default(o)


'''
Read and extract from the image
'''
def azure_extract(filepath):
    try:
        # Authenticate - prototype
        subscription_key    = "5b522eec6a7a429a86dc3a21ecb3a530"
        endpoint            = "https://loihub.cognitiveservices.azure.com/"

        # Init client
        credentials         = CognitiveServicesCredentials(subscription_key)
        client              = ComputerVisionClient(endpoint, credentials)

        # Images PDF with text
        filepath = open(filepath,'rb')

        # Async SDK call that "reads" the image
        response = client.read_in_stream(filepath, raw=True)
        print("Response:", response)

        # Don't forget to close the file
        filepath.close()

        # Get ID from returned headers
        operation_location = response.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]

        # SDK call that gets what is read
        while True:
            result = client.get_read_result(operation_id) # get_read_operation_result(operation_id)
            print('what is the result?', result)
            if result.status not in [OperationStatusCodes.not_started, OperationStatusCodes.running]:
                break
            time.sleep(1)
        return result

    except Exception as error:
        print("Problem setting up azure client", error)
        return False


def annotate_pdf(file_path, match_record):
    print("Annotation called.")
    pdf = PdfAnnotator(file_path)
    print("Attempting notations.")

    dpi_scalar = 72
    scale_offset = 792
    entity_keys = ['dd', 'closing', 'deposit', 'purchaseprice']

    for entity_key in entity_keys:
        try:
            box = match_record[entity_key]["analyze_meta"]["bounding_box"]
            location = Location(
                points = [
                    [box[0] * dpi_scalar, abs((box[1] * dpi_scalar) - scale_offset)], 
                    [box[2] * dpi_scalar, abs((box[3] * dpi_scalar) - scale_offset)], 
                    [box[4] * dpi_scalar, abs((box[5] * dpi_scalar) - scale_offset)],
                    [box[6] * dpi_scalar, abs((box[7] * dpi_scalar) - scale_offset)]
                ], 
                page = match_record[entity_key]["analyze_meta"]["page"] - 1
            )
            appearance = Appearance(
                stroke_color = (0, 1, 0), 
                stroke_width = 2
            )
            pdf.add_annotation('polygon', location, appearance)
            pdf.write(file_path)
        except KeyError as k:
            print(f"No match record for {k}")
        except Exception as e:
            print(f"Problem annotating entity {entity_key}: {e}")

# Create your views here.
### ALso need to install model via: python -m spacy download en_core_web_sm
@background(schedule=0)
def worker_process_doc(file_path, doc_id = False, deal_id = False):

    # get bid doc record, set status
    doc = BidDoc.objects.get(pk = doc_id)
    doc.status = 1
    doc_result = doc.save()

    print("Fetching file...", doc, file_path)
    try:
        print("Creating new entry..")
        entry = BidDocStats.objects.create(
            original_doc_name = file_path, # A bit redunant but this is for anlaytics
            start             = datetime.now()
        )
    except Exception as error:
        print('Failed to fetch', error)
        return

    credentials = dict(
        subscription_key    = os.environ['azure_subscription_key'],
        endpoint            = os.environ['azure_endpoint']
    )

    azure = AzureVisionService(credentials = credentials)

    try :
        
        ## Get result response from Azure services
        result = azure.get_ocr(file_path)
        
        ## Documents stats
        stats = azure.get_result_stats(result)
        
        match_record = dict(
            document   = file_path.split("/")[-1],
            pages      = stats['n_pages'],
        )
        
        ## Convert result to easily reference for matching later
        tokens             = azure.get_tokens(result, by_offset=False)
        tokens_punctuation = azure.get_token_punctuation(tokens)
        
        ## Intiialize entity matching methods
        matching = EntityRegexMatch(tokens = tokens)

        ## Initialize default NER model/Spacy object -- will train better model later
        document     = matching.get_document_token_pipeline(tokens = tokens_punctuation)
        # print("document pipeline", doc.vocab.vectors.data.shape)
        # match_record['doc'] = doc

        ## Get regex matches from fulltext based concatenated OCR service results
        matches      = matching.get_entity_matches(document.text)
        matches      = matching.update_sequence_entities_to_matches(document, matches)
        
        entity_map = dict(
            purchaseprice = "MONEY",
            deposit       = "MONEY",
            dd            = "DATE",
            closing       = "DATE",
        )
        entity_map[False] = False
        
        if not matches:
            return
        for index, match in enumerate(matches):
            
            entities              = match.get('entities', {})
            print("entities are:", entities)
            entity_strategy       = entity_map[match['entity_name']]
            best_entity_index     = matching.get_best_entity(entities, strategy = entity_strategy)
            # print("Best entity index:", best_entity_index, "entites:", entities)
            
            if type(best_entity_index) == int:
                best_match        = match['entities'][best_entity_index]
                ## Get the token from the best match and reference the index for the Azure coordinates
                best_match_token  = best_match['tokens'][0]
                best_match['analyze_meta'] = tokens_punctuation[best_match_token['token_index']]
                print("best match index:", tokens_punctuation[best_match_token['token_index']])
#                 best_match['coords'] = tokens_punctuation
                best_match_label  = best_match['label']
                best_match_text   = best_match['text']
            else:
                entities          = False
                best_match        = False
                best_match_label  = False
                best_match_text   = False
            
            ## Get first 
            if not match_record.get(match['entity_name'], False):
                match_record[match['entity_name']] = best_match
            
    except Exception as error:
        print("error!", error)
        logging.error("Error is:", error)


    print("About to annotate pdf..")


    annotate_pdf(file_path, match_record)


    print("About to update the document record")
    # Initialize new doc instance, update status to "2", ready for action
    try:
        print("Updating document record with new status..")
        doc = BidDoc.objects.get(pk = doc_id)
        logging.info(f'Fetching doc {doc_id}, {doc}')
        doc.status = 2
        doc.text            = document.text
        doc.word_coords     = match_record # dict(words = word_coords, status = "ok"),
        logging.info(f'Saving doc record with new data: {doc_id}')
        result = doc.save()
        logging.info(f'Saved doc: {doc_id}')
    except Exception as error:
        print("Couldn't save doc recrod", error)
        logging.info(f"Couldn't save doc record:", error)


## Old version of background process -- Will be removing 
def legacy_worker_process_doc(file_path, doc_id = False, deal_id = False):
    # from django.conf import settings
    from .forms import BidForm, BidDocForm
    from .doctools import DocTools
    
    print("Background process started...")

    # get bid doc record, set status
    doc = BidDoc.objects.get(pk = doc_id)
    doc.status = 1
    doc_result = doc.save()

    print("Fetching file...", doc, file_path)
    try:
        entry = BidDocStats.objects.create(
            original_doc_name = file_path, # A bit redunant but this is for anlaytics
            start             = datetime.now()
        )
    except Exception as error:
        print('Failed to fetch', error)
        return

    print("Created stats entry", entry)
    # entry.bid_doc       = new_doc.pk # Doesn't seem to like original reference

    # Converting 
    dt  = DocTools(django_settings = settings)

    source      = f"{deal_id}/{doc.original_doc_name}"
    source_path = f"{deal_id}/"

    img_filepath        =   dt.pdf_to_image(source, source_path)            # 1. Converts initial PDF doc to image, returns image location
    pdf_filepath        =   dt.image_to_pdf(img_filepath)                   # 2. Converts image to "searchable pdf"
    doctext, word_coords =  dt.pdf_to_text_coordinates(pdf_filepath)        # 3. Get document text from PDF, then get coordinates of each word

    if word_coords:
        ## super annoying but convert decimal type to float
        word_coords = [{name: float(value) if type(value) == decimal.Decimal else value for name, value in row.items()} for row in word_coords]

    dt.logging.info('Done processing docs..')

    # Initialize new doc instance, update status to "2", ready for action
    try:
        doc = BidDoc.objects.get(pk = doc_id)
        dt.logging.info(f'Fetching doc {doc_id}, {doc}')
        doc.status = 2
        doc.text            = doctext
        doc.word_coords     = dict(words = word_coords, status = "ok"),
        dt.logging.info(f'Saving doc record with new data: {doc_id}')
        result = doc.save()
        dt.logging.info(f'Saved doc: {doc_id}')
    except Exception as error:
        dt.logging.info(f"Couldn't save doc record:", error)

    try:
        dt.logging.info("Starting Azure request...")
        azure_start               = time.time()
        azure_results = azure_extract(file_path)
        azure_end                 = time.time()
        dt.logging.info("Azure results successful...")
  
    except Exception as error:
        dt.logging.info("Problem getting azure results...")

    dt.logging.info("Fetching stat object.")
    entry               = BidDocStats.objects.get(pk = entry.pk)
    dt.logging.info("Setting stat attributes.")
    entry.biddoc        = doc
    entry.end           = datetime.now()
    dt.logging.info("Setting result attribute.")
    try:
        entry.results       = dict(
            extracts = dict(
                pytesseract = dict(
                    words   = doc.word_coords,
                    doctext = doctext,
                ),
                azure = dict(
                    results = azure_results.as_dict(),
                    start   = azure_start,
                    end     = azure_end,
                    duration = azure_end - azure_start
                )
            ),
        )
    except Exception as error:
        print("There was a problem with setting reuslts:", error)

    dt.logging.info("Done setting stat attributes.")
    try:
        print("Before bidstats save...")
        entry.save()
        print("Saved bidstats results.")
    except Exception as error:
        dt.logging.info(f"Couldn't save biddoc stats record: {error}")
        

class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, **kwargs):
        print(self.request.FILES)
        if self.request.POST.get('filename', False):
            print("KWARGS", self.request, kwargs)
            deal_id = self.kwargs['pk']
            filename = self.request.POST['filename']
            file_obj = self.request.FILES['file']

            file_upload_folder                  = f'{settings.DRF_FILE_UPLOAD_PATH}/{deal_id}/'
            request_data                        = dict(self.request.POST)
            request_data['doc_type']            = 1 # TBD:  code a file type validator
            request_data['deal']                = deal_id
            request_data['original_doc_name']   = file_obj.name
            request_data['user']                = request.user.id
            print("request_data: ", request_data)
            form                                = BidDocForm(request_data)

            if form.is_valid():
                biddoc_result = form.save()
                print('Results of biddoc save:', biddoc_result)
                # biddoc_result = BidDoc.objects.create(dealdoc_id = dealdoc_result, bid_id = bid_result)
                if not os.path.exists(file_upload_folder):
                    print("Making direcory: ", file_upload_folder)
                    os.mkdir(file_upload_folder)

                file_save_path = f'{file_upload_folder}/{file_obj.name}'
                print('file_save_path = ', file_save_path)
                with open(file_save_path, 'wb+') as f:
                    for chunk in file_obj.chunks():
                        f.write(chunk)

                mime_type = magic.from_file(file_save_path, mime=True)


                if mime_type != "application/pdf":
                    return HttpResponse(content='Invalid File Type', status = 406)
                try:
                    ## Kick worker thread off to process the document
                    worker_process_doc(file_save_path, doc_id = biddoc_result.pk, deal_id = deal_id)
                    status  = 200
                    message = "File submitted for processing."
                except Exception as error:
                    status  = 500
                    message = f"worker offline.  Please recheck.  {error}"
            else:
                status = 500
                message = "File data invalid. " + str(form.errors)

            # do some stuff with uploaded file
            response = dict(
                status = status,
                message = message
            )
        else:
            response = dict(
                status = 200,
                message = "Files not included in request."
            )

        print(response,)
        return JsonResponse(response, status = 200, safe = True)


@csrf_exempt
def upload(request):
    if (request.POST):
        # file = request.FILES.get('filepond')
        fieldname, deal_id = get_deal_id(request.POST)
        print(request.get('POST'))
        if fieldname:
            file = request.FILES.get(fieldname)
            file_upload_folder = f'{settings.DRF_FILE_UPLOAD_PATH}/{deal_id}/'
            request_data = dict(request.POST)
            request_data['doc_type'] = 1 # TBD:  code a file type validator
            request_data['deal'] = deal_id
            request_data['original_doc_name'] = file.name
            request_data['user'] = request.user.id
            print("request_data: ", request_data)
            form=BidDocForm(request_data)
            if form.is_valid():
                biddoc_result = form.save()
                # reference DealDoc inserted id
                print("last biddoc_id: ", biddoc_result.pk)
                # insert blank bid, inserted from document
                # deal=Deal.objects.get(id=int(deal_id))
                # bid_result = Bid.objects.create(deal=deal, comments="created from file upload")
                # print("print last bid_id: ", bid_result.pk)
                # insert BidDoc record

                # biddoc_result = BidDoc.objects.create(dealdoc_id = dealdoc_result, bid_id = bid_result)
                if not os.path.exists(file_upload_folder):
                    print("Making direcory: ", file_upload_folder)
                    os.mkdir(file_upload_folder)

                file_save_path = f'{file_upload_folder}/{file.name}'
                print('file_save_path = ', file_save_path)
                with open(file_save_path, 'wb+') as f:
                    for chunk in file.chunks():
                        f.write(chunk)

                mime_type = magic.from_file(file_save_path, mime=True)
                if mime_type != "application/pdf":
                    return HttpResponse(content='Invalid File Type', status = 406)


                return HttpResponse(content='success', status=200)

            else:
                print('Form not valid.',form.errors, file.name)

        else:
            return HttpResponseNotFound('Error accessing file, not found.')
    else:
        return HttpResponseServerError('Error reading file...')


class DealCreate(CreateView):
    model = Deal
    fields = ['deal_name']
    template_name = 'bidinterpreter/deal_form.html'

    def form_valid(self, form):
        #super(DealCreate, self).save(*args, **kwargs)
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
        deal = Deal.objects.get(pk = self.kwargs['pk'])

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
        deal = Deal.objects.get(pk = self.kwargs['pk'])

        if deal.user and hasattr(deal.user, "id") and deal.user.id == self.request.user.id:
            deal_owner = True
        else:
            deal_owner = False

        if deal_owner:
            return super().dispatch(*args, **kwargs)
      
        raise Http404


class BidListView(SingleTableView):
    model = Bid
    table_class = BidTable
    template_name = 'bidinterpreter/bid_list.html'


class BidUpdate(UpdateView):
    model = Bid
    #fields = '__all__'
    template_name = 'bidinterpreter/create_bid.html'
    form_class = BidForm
    # success_url = reverse_lazy('bidinterpreter:detail')

    def dispatch(self, *args, **kwargs):
        print('dispatch running...')
        bid = Bid.objects.get(pk = self.kwargs['pk'])

        if bid.user and hasattr(bid.user, "id") and bid.user.id == self.request.user.id:
            bid_owner = True
        else:
            bid_owner = False

        # Checking permissions -- the "hard" way
        users_can_bid   = User.objects.filter(groups__name = f"group_{bid.deal.pk}_can_bid")
        users_view_only = User.objects.filter(groups__name = f"group_{bid.deal.pk}_view_only")

        bid_users  = users_can_bid
        view_users = users_view_only 

        user_can_bid_ids    = [user.pk for user in users_can_bid]
        users_view_only_ids = [user.pk for user in users_view_only]

        if bid_owner or self.request.user.pk in user_can_bid_ids:
            return super().dispatch(*args, **kwargs)
      
        raise Http404

    def get_context_data(self, **kwargs):
        
        from decimal import Decimal

        # print(self.kwargs)
        context = super().get_context_data(**kwargs)
        context['update'] = True
        context['deal_name'] = Deal.objects.get(id=self.object.deal_id)
        context['deal_id'] = self.object.deal_id

        ## data for static example
        doc = BidDoc.objects.get(pk = 29)

        source = f"1/{doc.original_doc_name}"

        doctext, word_coords = doc.text, doc.word_coords
        
        ## Convert back to decimal for legacy code -- we use JSON type for widget in backend.


        # matches             =   dt.get_entity_matches(doctext, word_coords)      # 4. Extract matches /w coordinates
        # hilight_coords      =   dt.image_to_highlighted(matches, pdf_filepath, img_filepath)
        # entities            =   dt.map_entities(pdf_filepath, word_coords, doctext = doctext, vocabulary = word_coords)
        #
        # context['letter_coords']    =   word_coords
        # context['hilight_coords']   =   hilight_coords
        # context['matches']          =   matches
        # context['entities']         =   entities

        context["pdf_url"] = source

        return context

    def get_success_url(self):
        view_name = 'bidinterpreter:detail'
        # No need for reverse_lazy here, because it's called inside the method
        return reverse(view_name, kwargs={'pk': self.object.deal_id})

    def form_valid(self, form):
        
        logger.info('form_valid called')

        self.object = form.save(commit=False)  
        if self.request.user.is_authenticated:
            self.object.user = self.request.user
        # Another computing etc
        self.object.save()
        ## Update biddoc 
        if self.request.POST.get('bid_doc'):
            print("attempting to update biddoc status to 3")
            doc = BidDoc.objects.get(pk = self.request.POST.get('bid_doc'))
            doc.status = 3 # 3 = new bid
            doc.bid = self.kwargs['pk']
            doc.save()
        return super(BidUpdate, self).form_valid(form)
    

class BidDelete(DeleteView):
    model = Bid

    def dispatch(self, *args, **kwargs):
        bid = Bid.objects.get(pk = self.kwargs['pk'])

        if bid.user and hasattr(bid.user, "id") and bid.user.id == self.request.user.id:
            bid_owner = True
        else:
            bid_owner = False

        # Checking permissions -- the "hard" way
        users_can_bid   = User.objects.filter(groups__name = f"group_{bid.deal.pk}_can_bid")
        users_view_only = User.objects.filter(groups__name = f"group_{bid.deal.pk}_view_only")

        bid_users  = users_can_bid
        view_users = users_view_only 

        print('can bid users', users_can_bid)

        user_can_bid_ids    = [user.pk for user in users_can_bid]
        users_view_only_ids = [user.pk for user in users_view_only]

        if bid_owner or self.request.user.pk in user_can_bid_ids:
            return super().dispatch(*args, **kwargs)
      
        raise Http404

    def get(self,request,*args,**kwargs):
        return self.post(request,*args,**kwargs)

    # success_url = reverse_lazy('bidinterpreter:index')

    def get_success_url(self):
        view_name = 'bidinterpreter:detail'
        # No need for reverse_lazy here, because it's called inside the method
        return reverse(view_name, kwargs={'pk': self.object.deal_id})


# named route: bid-add
class BidCreate(CreateView):
    model = Bid
    # fields = ['bidder', 'purchase_price', 'due_diligence', 'closing', 'comments', 'deposit', 'date_received']
    template_name   = 'bidinterpreter/create_bid.html'
    form_class      = BidForm
    session_element_map = dict(
        purchaseprice   = 'purchase_price',
        dd              = 'due_diligence',
        closing         = 'closing',
        deposit         = 'deposit'
    )
    entity_keys = ['dd', 'closing', 'deposit', 'purchaseprice']


    def post(self, request, *args, **kwargs):
        # cleaned_data = super(IncidentForm, self).clean()
        self.object = self.get_object() # not sure why this is necessary but throws error if not
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        updated_request = self.request.POST.copy()

        to_format = ["purchase_price", "deposit"]
        to_remove = ["$", ","]

        for key in to_format:
            value = form.data.get(key, "")
            for char in to_remove:
                value = value.replace(char, "")
            updated_request[key] = float(value)
        return super().post(updated_request, *args, **kwargs)

    def form_invalid(self, form):
        print("form invalid running")
        return super(BidCreate, self).form_invalid(form)

    def form_valid(self, form):
        
        logger.info('form_valid called')
        form.instance.user = self.request.user

        updated_request = self.request.POST.copy()
        updated_request['user'] = self.request.user

        form.instance.save(updated_request)
      
        ## Update biddoc 
        if self.request.POST.get('bid_doc_id'):
            print("bid doc status")
            doc = BidDoc.objects.get(pk = self.request.POST.get('bid_doc_id'))
            doc.status = 3 # 3 = new bid
            doc.bid_id = self.kwargs['pk']
            result = doc.save()
            print("save result:", result)

        messages.success(self.request, 'Bid Created Successfully')
        return redirect('bidinterpreter:detail', pk=self.kwargs.get('pk'))
        return self.render_to_response(self.get_context_data())
        # return super(BidCreate, self).form_valid(form)

    def get_initial(self):
        import locale
        initial = {
            'deal':  self.kwargs.get('pk'),
            'user':  self.request.user,
        }

        doc = BidDoc.objects.get(pk=self.request.GET.get('bid_doc_id'))
        entities = doc.word_coords
      
        # print("self form:", dir(self.form_class), self.model._meta.fields)
        for field in self.model._meta.fields:
            var_name  = field.name
            var_value = self.request.GET.get(var_name, False) # only check fields defined by the model
            if var_value and field.get_internal_type() in ['DecimalField', int]:
                initial[var_name] = float(var_value.replace("$", "").replace(",", "") if "$" in var_value else var_value)
            elif var_value:
                initial[var_name] = var_value

        initial['bid_doc'] = self.request.GET.get('bid_doc_id', "")
        
        # Get extracted entities here and create auto override
        for entity_key, database_field in self.session_element_map.items():
            if not initial.get(database_field) and entities.get(entity_key, False):
                if database_field == "purchase_price":
                    # last minute hack -- TBD update to better solution
                    entities[entity_key]['text'] = re.sub("[^0-9.]", "", entities[entity_key]['text'])
                    
                initial[database_field] = entities[entity_key]['text']

        # form        = self.get_form(form_class)
        

        ## Depricated to allow form values sent from doc import view
        # session_doc = self.get_session_doc()
        # if session_doc:
        #     for session_key, model_element in self.session_element_map.items():
        #         if session_doc.get(session_key, False):
        #             ## Quick hack to format number for numeric/decimal fields
        #             session_doc[session_key] = session_doc[session_key].replace("$", "").replace(",", "") if "$" in session_doc[session_key] else session_doc[session_key]
        #             initial[model_element]   = session_doc[session_key]

        return initial

    def get_context_data(self, **kwargs):
        # print(self.kwargs)
        context = super(BidCreate, self).get_context_data(**kwargs)
        doc = BidDoc.objects.get(pk=self.request.GET.get('bid_doc_id'))
        source = f"{doc.deal_id}/{doc.original_doc_name}"
        doctext, word_coords = doc.text, doc.word_coords

        # Check if session token matches form token
        session_doc = self.get_session_doc()
        if session_doc:
            # print("tokens match we have a document data to import", session_doc.keys())
            context['document_import']          = True
            context['original_document_name']   = session_doc['original_document_name']
            context['datetime']                 = datetime.strptime(session_doc['datetime'], '%Y-%m-%d %H:%M:%S.%f')

        context['document_import'] = True
        context['original_document_name'] = doc.original_doc_name
        # context['datetime'] = datetime.strptime(session_doc['datetime'], '%Y-%m-%d %H:%M:%S.%f')
        context['pdf_url'] = source
        context['deal_id'] = self.kwargs.get('pk')
        context['deal_name'] = Deal.objects.get(id=context['deal_id'])
        context['deal_doc_id'] = self.kwargs.get('bid_doc_id')

        ## entity page numbers for scrolling
        entities = {}
        if type(word_coords) == dict:
            for entity_key, config in word_coords.items():
                if type(config) == dict:
                    entities[entity_key] = config['analyze_meta']['page']
        context['entities'] = mark_safe(json.dumps(entities))
        

        ## set form data from processed doc if exists (we may want to rename the database field from word_coords)
        
        for entity_key in self.entity_keys:
            try:
                context[entity_key] = word_coords[entity_key]['text']
            except Exception as e:
                print(f"No entity to set for {entity_key}: {e}")

        # print(dir(self))
        return context
    
    def get_session_doc(self):
        # Check session for document import
        session_token = self.request.session.get('import_doc', {}).get('p', False)
        form_token = self.request.GET.get('p', False)
        if all([session_token, form_token]) and session_token == form_token:
            return self.request.session.get('import_doc')
        else:
            return False


class SearchView(TemplateView):
    template_name = "bidinterpreter/search.html"


class JSONSearch(DetailView):
    def filter_by_group_permission(self, queryset, term):
        user_groups = set(self.request.user.groups.values_list('name', flat = True))
        exclude_group_ids = []
        
        for row in queryset:
            group_id = row.id
            user     = row.user

            # Check if deal has a user
            if user and hasattr(user, "id"):
                user_id = row.user.id 
            else:
                user_id = False 

            # qualified groups
            groups = set([f"group_{row.id}_view_only", f"group_{row.id}_can_bid"])
            group_intersection = user_groups.intersection(groups)
             
            if group_intersection == set() and user_id != self.request.user.id:
                exclude_group_ids.append(group_id)
        print("This is the end..")
        return Deal.objects.exclude(id__in =exclude_group_ids).filter(deal_name__icontains=term)

    def get(self, request, *args, **kwargs):
        deals_filtered = []
        if 'term' in self.request.GET:
            term = self.request.GET.get('term')
            deals = Deal.objects.filter(deal_name__icontains=term)
            filtered_deals = self.filter_by_group_permission(deals, term)
            for deal in filtered_deals:
                deals_filtered.append({
                    'id':    deal.id,
                    'name':  deal.deal_name,
                    'owner': {
                        'username': deal.user.username,
                        'avatar':   deal.user.socialaccount_set.filter(provider='google')[0].extra_data['picture']
                    }
                })
        return JsonResponse(deals_filtered,safe=False)

class SearchPluginView(TemplateView):
    template_name = "bidinterpreter/searchplugin.html"

def SearchPluginJSON(request):
    deals_filtered = []
    if 'term' in request.GET:
        print('term exists')
        term = request.GET.get('term')
        deals = Deal.objects.filter(deal_name__icontains=term)
        for deal in deals:
            deals_filtered.append(deal.deal_name)
        print(deals)
    return JsonResponse(deals_filtered,safe=False)
