from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.generic.base import View
from django.utils.encoding import smart_str
from sqlalchemy import create_engine # Likely a better way to do this.
from io import StringIO, BytesIO
import pandas as pd
import os

## matplotlib for PDF processing
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .models import Deal

# SQL used in both methods
## Should be same as statement from views.py deal summary route.
sql = """
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

def normalize_deal_name(deal_name):
    
    to_remove = "()[]&^%$#@!;':\",.<>/?"

    for char in list(to_remove):
        deal_name = deal_name.replace(char, "")

    ## remove spaces
    deal_name = deal_name.lower().replace(" ", "_")
    return deal_name

class DownloadCSV(View):

    # Set the content type value
    content_type = 'text/csv'

    def get(self, request, **kwargs):

        host, port, database, user, password  = (
            os.environ['pgsql_host'],
            os.environ['pgsql_port'],
            os.environ['pgsql_db'],
            os.environ['pgsql_user'],
            os.environ['pgsql_password'],
        )

        ## Get deal name
        deal = Deal.objects.get(pk = kwargs['pk'])
        filename = smart_str(kwargs.get('pk') + "-" + normalize_deal_name(deal.deal_name))

        ## connect to database using SQLalchemy
        conn        = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")
        df          = pd.read_sql(sql.format(deal_id = kwargs.get('pk')), con = conn)
        csv_data    = StringIO()

        ## Write csv datat to stringIO stream
        df.to_csv(csv_data)

        ## Push data as attachment for response
        response = HttpResponse(csv_data.getvalue(), content_type = self.content_type)
        response["Content-Disposition"] = f'attachment; name="{filename}"; filename="{filename}.csv"'
        return response


class DownloadPDF(View):
    # Set the content type value
    content_type = 'application/pdf'

    def get(self, request, **kwargs):

        host, port, database, user, password  = (
            os.environ['pgsql_host'],
            os.environ['pgsql_port'],
            os.environ['pgsql_db'],
            os.environ['pgsql_user'],
            os.environ['pgsql_password'],
        )

        ## Get deal name
        deal = Deal.objects.get(pk = kwargs['pk'])
        filename = smart_str(kwargs.get('pk') + "-" + normalize_deal_name(deal.deal_name))

        ## connect to database using SQLalchemy
        conn        = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")
        df          = pd.read_sql(sql.format(deal_id = kwargs.get('pk')), con = conn)
        pdf_data    = BytesIO()

        ## matplotlib code
        fig, ax = plt.subplots(figsize=(25,25))
        # ax.axis('tight')
        ax.axis('off')

        table = ax.table(cellText=df.values,colLabels=df.columns,loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        for k, cell in table._cells.items():
            cell.set_text_props(wrap = True)
            cell.set_height(.01)
        table.scale(1, 4)

        ## Write csv datat to stringIO stream
        pdf = PdfPages(pdf_data)
        pdf.savefig(fig, bbox_inches='tight')
        pdf.close()

        ## Push data as attachment for response
        response = HttpResponse(pdf_data.getvalue(), content_type = self.content_type)
        response["Content-Disposition"] = f'attachment; name="{filename}"; filename="{filename}.pdf"'
        return response