from datetime import datetime

from django.http import Http404
from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import redirect, render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse
from django.contrib import messages

from django_tables2 import SingleTableView


from .models import Deal, Bid, BidDoc
from .forms import BidForm, BidDocForm
from .tables import BidTable
## Prototype extract data and coordinates
from .doctools import DocTools




import logging, decimal

logger = logging.getLogger(__name__)


class BidDetailView(SingleTableView):
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

        # bidset = Bid.objects.filter(deal=self.kwargs.get('pk')) # raw('SELECT bidinterpreter_bid.*, bidinterpreter_biddoc.* FROM bidinterpreter_bid LEFT JOIN bidinterpreter_biddoc ON bidinterpreter_bid.id = bidinterpreter_biddoc.bid_id WHERE deal_id='+self.kwargs.get('pk'))
        # .filter(deal=self.kwargs.get('pk'))
        # bidx = Bid.objects.prefetch_related('bid_set').get(deal='14')

        # qset = BidDoc.objects.select_related('bid').all()
        # filter(bid_deal=self.kwargs.get('pk'))
        bids = Bid.objects.raw(self.raw_sql.format(deal_id=self.kwargs.get('pk')))
        return bids

    #    # a1 = Bid.objects.filter(Bid__deal=self.kwargs.get('pk'))

    #     # return Bid.objects.filter(BidDoc__deal=self.kwargs.get('pk'))
    #     # return Bid.objects.filter(deal_id=self.kwargs.get('pk'))
    #     # .order_by('-pub_date')[:5]
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        ## TBD:  add count of items

        deal = Deal.objects.get(pk=self.kwargs.get('pk'))
        bids = self.get_queryset()
        context['deal'] = self.kwargs.get('pk')
        context['deal_name'] = deal
        context['table'] = BidTable(list(bids))
        context['bid_count'] = len(list(bids))
        context['owner_meta'] = deal.user

        # deal = Deal.objects.get(pk = context['deal'])

        print("deal user", deal.user)

        if deal.user and hasattr(deal.user, "id") and deal.user.id == self.request.user.id:
            context['deal_owner'] = True
        else:
            context['deal_owner'] = False

        # User count for subnav
        users_can_bid = User.objects.filter(groups__name=f"group_{context['deal']}_can_bid")
        users_view_only = User.objects.filter(groups__name=f"group_{context['deal']}_view_only")

        context['bid_users'] = users_can_bid
        context['view_users'] = users_view_only

        print('can bid users', users_can_bid)

        user_can_bid_ids = [user.pk for user in users_can_bid]
        users_view_only_ids = [user.pk for user in users_view_only]

        context['user_count'] = users_can_bid.count() + users_view_only.count()

        if self.request.user.id in user_can_bid_ids:
            context['can_bid'] = True

        if self.request.user.id in users_view_only_ids:
            context['view_only'] = True

            # context['docs'] = BidDoc.objects.filter(deal = context['deal'])
        # context['docs'] = BidDoc.objects.filter(bid_id=context['bid'])
        return context


class BidListView(SingleTableView):
    model = Bid
    table_class = BidTable
    template_name = 'bidinterpreter/bid_list.html'


class BidUpdate(UpdateView):
    model = Bid
    # fields = '__all__'
    template_name = 'bidinterpreter/create_bid.html'
    form_class = BidForm

    # success_url = reverse_lazy('bidinterpreter:detail')

    def dispatch(self, *args, **kwargs):
        print('dispatch running...')
        bid = Bid.objects.get(pk=self.kwargs['pk'])

        if bid.user and hasattr(bid.user, "id") and bid.user.id == self.request.user.id:
            bid_owner = True
        else:
            bid_owner = False

        # Checking permissions -- the "hard" way
        users_can_bid = User.objects.filter(groups__name=f"group_{bid.deal.pk}_can_bid")
        users_view_only = User.objects.filter(groups__name=f"group_{bid.deal.pk}_view_only")

        bid_users = users_can_bid
        view_users = users_view_only

        user_can_bid_ids = [user.pk for user in users_can_bid]
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
        dt = DocTools(django_settings=settings)
        doc = BidDoc.objects.get(pk=85)

        source = f"2/{doc.original_doc_name}"
        source_path = f"2/"

        img_filepath = source + ".png"  # TBD:  check this exists
        pdf_filepath = source + ".png.processed.pdf"  # TBD:  check this exists
        doctext, word_coords = doc.text, doc.word_coords

        ## Convert back to decimal for legacy code -- we use JSON type for widget in backend.
        word_coords = word_coords = [
            {name: Decimal(value) if type(value) == float else value
             for name, value in row.items()}
            for row in word_coords[0]['words']
        ]

        matches = dt.get_entity_matches(doctext, word_coords)  # 4. Extract matches /w coordinates
        hilight_coords = dt.image_to_highlighted(matches, pdf_filepath, img_filepath)
        entities = dt.map_entities(pdf_filepath, word_coords, doctext=doctext, vocabulary=word_coords)

        context['letter_coords'] = word_coords
        context['hilight_coords'] = hilight_coords
        context['matches'] = matches
        context['entities'] = entities

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
            doc = BidDoc.objects.get(pk=self.request.POST.get('bid_doc'))
            doc.status = 3  # 3 = new bid
            doc.bid = self.kwargs['pk']
            doc.save()
        return super(BidUpdate, self).form_valid(form)


class BidDelete(DeleteView):
    model = Bid

    def dispatch(self, *args, **kwargs):
        bid = Bid.objects.get(pk=self.kwargs['pk'])

        if bid.user and hasattr(bid.user, "id") and bid.user.id == self.request.user.id:
            bid_owner = True
        else:
            bid_owner = False

        # Checking permissions -- the "hard" way
        users_can_bid = User.objects.filter(groups__name=f"group_{bid.deal.pk}_can_bid")
        users_view_only = User.objects.filter(groups__name=f"group_{bid.deal.pk}_view_only")

        bid_users = users_can_bid
        view_users = users_view_only

        print('can bid users', users_can_bid)

        user_can_bid_ids = [user.pk for user in users_can_bid]
        users_view_only_ids = [user.pk for user in users_view_only]

        if bid_owner or self.request.user.pk in user_can_bid_ids:
            return super().dispatch(*args, **kwargs)

        raise Http404

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    # success_url = reverse_lazy('bidinterpreter:index')

    def get_success_url(self):
        view_name = 'bidinterpreter:detail'
        # No need for reverse_lazy here, because it's called inside the method
        return reverse(view_name, kwargs={'pk': self.object.deal_id})


# named route: bid-add
class BidCreate(CreateView):
    model = Bid
    # fields = ['bidder', 'purchase_price', 'due_diligence', 'closing', 'comments', 'deposit', 'date_received']
    template_name = 'bidinterpreter/create_bid.html'
    form_class = BidForm
    session_element_map = dict(
        purchaseprice='purchase_price',
        dd='due_diligence',
        closing='closing',
        deposit='deposit'
    )

    # def form_invalid(self, form):
    #     print("form is invalid for some reason")

    # def post(self, request, *args, **kwargs):
    #     # cleaned_data = super(IncidentForm, self).clean()
    #     self.object = self.get_object() # not sure why this is necessary but throws error if not
    #     form_class = self.get_form_class()
    #     form = self.get_form(form_class)
    #     updated_request = self.request.POST.copy()

    #     to_format = ["purchase_price", "deposit"]
    #     to_remove = ["$", ","]

    #     for key in to_format:
    #         value = form.data.get(key, "")
    #         for char in to_remove:
    #             value = value.replace(char, "")
    #         updated_request[key] = float(value)
    #     return super().post(updated_request, *args, **kwargs)

    # def form_invalid(self, form):
    #     print("form invalid running")
    #     return super(BidCreate, self).form_invalid(form)

    def form_valid(self, form):

        logger.info('form_valid called')
        form.instance.user = self.request.user

        updated_request = self.request.POST.copy()
        updated_request['user'] = self.request.user

        form.instance.save(updated_request)

        ## Update biddoc
        if self.request.POST.get('bid_doc_id'):
            print("bid doc status")
            doc = BidDoc.objects.get(pk=self.request.POST.get('bid_doc_id'))
            doc.status = 3  # 3 = new bid
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
            'deal': self.kwargs.get('pk'),
            'user': self.request.user,
        }
        # print("self form:", dir(self.form_class), self.model._meta.fields)
        for field in self.model._meta.fields:
            var_name = field.name
            var_value = self.request.GET.get(var_name, False)  # only check fields defined by the model
            if var_value and field.get_internal_type() in ['DecimalField', int]:
                initial[var_name] = float(
                    var_value.replace("$", "").replace(",", "") if "$" in var_value else var_value)
            elif var_value:
                initial[var_name] = var_value

        initial['bid_doc'] = self.request.GET.get('bid_doc_id', "")
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
        context['deal_id'] = self.kwargs.get('pk')
        context['deal_name'] = Deal.objects.get(id=context['deal_id'])
        context['deal_doc_id'] = self.kwargs.get('bid_doc_id')

        # Check if session token matches form token
        session_doc = self.get_session_doc()
        if session_doc:
            # print("tokens match we have a document data to import", session_doc.keys())
            context['document_import'] = True
            context['original_document_name'] = session_doc['original_document_name']
            context['datetime'] = datetime.strptime(session_doc['datetime'], '%Y-%m-%d %H:%M:%S.%f')

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
