from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth import get_user_model
from .models import Deal, DealInvite, Bid, BidDoc
from django.utils.html import format_html
from django.contrib.humanize.templatetags import humanize

from django_tables2 import tables, SingleTableView, TemplateColumn, CheckBoxColumn
import django_tables2 as tables
from django_tables2.config import RequestConfig

class CurrencyFormat(tables.Column):
    def render(self, value):
        return '${:,.0f}'.format(value)

templates = dict(
    bid_actions = '''
    {% if record.user_id == request.user.id or deal_owner or request.user in bid_users  %}
        {% if record.pk != None %}
            <a href="{% url 'bidinterpreter:bid-update' record.pk %}"><i class="fas fa-edit" title="Edit/Review"></i></a>
            <a href="{% url 'bidinterpreter:bid-delete' record.pk %}" name="delete_bid"><i class="fas fa-trash-alt" title="delete"></i></a>
        {% elif record.doc_status == 2 %}
            <a href="/bidinterpreter/deal/{{record.deal_id}}/add_bid/?bid_doc_id={{record.doc_id}}" class="btn btn-sm btn-success" style="white-space: nowrap;"><i class="fas fa-magic" aria-hidden="true"></i> Review</a>
        {% endif %}
    {% endif %}
    ''',
    user_invite_actions = '''
{% if record.user_id == request.user.id or deal_owner %}
    {% if record.pk != None %}
        <a href="{% url 'bidinterpreter:invite-delete' record.deal.id record.pk %}" name="delete_bid"><i class="fas fa-trash-alt" title="delete"></i></a>
    {% endif %}
{% endif %}
''',
    user_invite_link = '''
{% if record.user_id == request.user.id or deal_owner %}
    {% if record.pk != None %}
        <a href="https://staging.loihub.com:8002/invite/{{record.unique_id}}" target="_blank">Invite</a>
    {% endif %}
{% endif %}
'''
)

class BidTable(tables.Table):
    action = TemplateColumn(templates['bid_actions'])
    purchase_price = CurrencyFormat(verbose_name= 'Price')

    doc_status_map = {
        0: format_html('<span class="badge badge-primary">new</span>'),
        1: format_html('<span class="badge badge-warning">processing</span>'),
        2: format_html('<span class="badge badge-success">ready</span>'),
        3: format_html('<span class="badge badge-primary">submitted</span>')
    }

    def __init__(self, *args, date_verbose_name="",**kwargs):
        super().__init__(*args, **kwargs)
        self.base_columns['doc_status'].verbose_name            = "Status"
        self.base_columns['original_doc_name'].verbose_name     = "Document"
        # self.base_columns['doc_created'].verbose_name           = "Uploaded"
        self.base_columns['created'].verbose_name         = "Updated"

    def render_created(self, value, column):
        return humanize.naturaltime(value)

    # def render_date_uploaded(self, value, column):
    #     return humanize.naturaltime(value)

    def render_original_doc_name(self, value, column):
        return format_html(f"<span style='white-space: nowrap;' title='{value}'>{value[0:20]}...</span>")

    def render_doc_status(self, value, column):
        print("value:", value, "column:", column)

        return self.doc_status_map.get(value, "Error Processing")

    class Meta:
        model = Bid
        template_name   = 'django_tables2/bootstrap.html'
        fields          = ['id', 'doc_id', 'doc_status', 'bid_status', 'user', 'original_doc_name', 'purchase_price', 'deposit', 'due_diligence', 'closing', 'created']
        exclude         = ['id', 'doc_id', 'bid_status', 'deposit', 'due_diligence', 'closing']
        row_attrs       = { "class": lambda record: "table-success" if record.doc_status == 2 else "" }
        attrs           = { "thead": { "class": "thead-dark"}, "class": "table bid-table table-striped table-hover"}


class DealUserTable(tables.Table):
    # action = TemplateColumn(TEMPLATE)
    # purchase_price = CurrencyFormat(verbose_name= 'Price')
    permission =  tables.Column(empty_values=())

    action = CheckBoxColumn(accessor='pk', attrs = { 
        "th__input": {
            "onclick": "toggle(this)"
        }
    }, orderable=False)

    def render_permission(self, record):
        
        ## Lookup permissions
 
        deal_id   = record.deal_id
        try:
            can_bid   = [user.id for user in Group.objects.get(name=f"group_{deal_id}_can_bid").user_set.all()]

        except:
            can_bid = []

        try:
            view_only = [user.id for user in Group.objects.get(name=f"group_{deal_id}_view_only").user_set.all()]
        except:
            veiw_only = []

        # If user in bid group display bid group label
        if record.id in can_bid:
            return format_html('<span class="badge badge-success">can bid</span>')
        else:
            return format_html('<span class="badge badge-secondary">view only</span>')

    # doc_status_map = {
    #     0: format_html('<span class="badge badge-primary">new</span>'),
    #     1: format_html('<span class="badge badge-warning">processing</span>'),
    #     2: format_html('<span class="badge badge-success">ready</span>'),
    #     3: format_html('<span class="badge badge-primary">submitted</span>')
    # }

    # def __init__(self, *args, date_verbose_name="",**kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.base_columns['doc_status'].verbose_name            = "Status"
    #     self.base_columns['original_doc_name'].verbose_name     = "Document"
    #     self.base_columns['doc_created'].verbose_name           = "Uploaded"
    #     self.base_columns['date_uploaded'].verbose_name         = "Updated"

    # def render_doc_created(self, value, column):
    #     return humanize.naturaltime(value)

    # def render_date_uploaded(self, value, column):
    #     return humanize.naturaltime(value)

    # def render_original_doc_name(self, value, column):
    #     return format_html(f"<span style='white-space: nowrap;' title='{value}'>{value[0:20]}...</span>")

    # def render_doc_status(self, value, column):
    #     print("value:", value, "column:", column)

    #     return self.doc_status_map.get(value, "Error Processing")

    class Meta:
        model = User
        template_name   = 'django_tables2/bootstrap.html'
        fields          = ['deal_id', 'permission', 'id', 'username', 'first_name', 'last_name', 'email']
        exclude         = ['deal_id']
        # exclude         = ['id', 'doc_id', 'bid_status', 'deposit', 'due_diligence', 'closing']
        # row_attrs       = { "class": lambda record: "table-success" if record.doc_status == 2 else "" }
        attrs           = { "thead": { "class": "table-secondary"}, "class": "table bid-table table-striped table-hover"}

# External invite table meta config
class DealInviteTable(tables.Table):
    action = TemplateColumn(templates['user_invite_actions'])
    link = TemplateColumn(templates['user_invite_link'])
    user_permission = tables.Column(verbose_name= 'Permission' )
    # purchase_price = CurrencyFormat(verbose_name='Price')

    doc_status_map = {
        0: format_html('<span class="badge badge-primary">new</span>'),
        1: format_html('<span class="badge badge-warning">processing</span>'),
        2: format_html('<span class="badge badge-success">ready</span>'),
        3: format_html('<span class="badge badge-primary">submitted</span>')
    }

    # def __init__(self, *args, date_verbose_name="",**kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.base_columns['doc_status'].verbose_name            = "Status"
    #     self.base_columns['original_doc_name'].verbose_name     = "Document"
    #     self.base_columns['doc_created'].verbose_name           = "Uploaded"
    #     self.base_columns['date_uploaded'].verbose_name         = "Updated"

    def render_user_permission(self, value, column):

        permission = {
            0: format_html('<span class="badge badge-primary">view only</span>'),
            1: format_html('<span class="badge badge-success">can bid</span>'),
        }

        return permission.get(value, format_html('<span class="badge badge-danger">error</span>'))

    def render_status(self, value, column):

        status = {
            -1: format_html('<span class="badge badge-warning">sent</span>'),
            0:  format_html('<span class="badge badge-primary">viewed</span>'),
            1:  format_html('<span class="badge badge-primary">registration</span>')
        }
        return status.get(value, format_html('<span class="badge badge-primary">error</span>'))

    def render_created(self, value, column):
        return humanize.naturaltime(value)

    def render_viewed(self, value, column):
        return humanize.naturaltime(value) if value else '---'

    def render_original_doc_name(self, value, column):
        return format_html(f"<span style='white-space: nowrap;' title='{value}'>{value[0:20]}...</span>")

    def render_doc_status(self, value, column):
        print("value:", value, "column:", column)

        return self.doc_status_map.get(value, "Error Processing")

    class Meta:
        model = DealInvite
        template_name   = 'django_tables2/bootstrap.html'
        fields          = ['email', 'created', 'viewed', 'user_permission', 'status', 'link']
        exclude         = ['id', 'doc_id', 'bid_status', 'deposit', 'due_diligence', 'closing', 'price']
        attrs           = { "thead": { "class": "table-secondary"}, "class": "table bid-table table-striped table-hover"}
        # row_attrs       = { "class": lambda record: "table-success" if record.doc_status == 2 else "" }