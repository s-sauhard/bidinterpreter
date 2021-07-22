from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings 
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import TemplateView
import json, secrets
from .forms import BidForm, FormStepOne, FormStepTwo
from .models import BidDoc, Deal
from .doctools import DocTools
from formtools.wizard.views import SessionWizardView # Goign to phase this out
from django.contrib.humanize.templatetags import humanize

from datetime import datetime
from time import strftime

def test_json(request):
    print("basDIR", settings.BASE_DIR)
    json_file = f"{settings.BASE_DIR}/project/templates/bidinterpreter/import_test.json"
    with open(json_file) as f:
        data = json.load(f)
    return JsonResponse(data)


class ImportWizardView(TemplateView):
    template_name = "bidinterpreter/import_wizard_preview.html"
    def get_context_data(self, **kwargs):
        context = super(ImportWizardView, self).get_context_data(**kwargs)
        doc     = BidDoc.objects.get(pk = self.kwargs['doc_id'])
        deal    = Deal.objects.get(pk = self.kwargs['pk'])
        context['original_doc_name']    = doc.original_doc_name
        context['deal_id']              = doc.deal_id
        context['deal_name']            = deal.deal_name
        
        return context

    def get(self, request, *args, **kwargs):
        #self.object = self.get_object()
        data = self.get_context_data(**kwargs)
        
        if self.request.GET.get('format', False):
 
            # Converting 
            dt  = DocTools(django_settings = settings)
            doc = BidDoc.objects.get(pk = self.kwargs['doc_id'])

            source = f"{self.kwargs['pk']}/{doc.original_doc_name}"
            source_path = f"{self.kwargs['pk']}/"
     
            token                = secrets.token_urlsafe()
            from decimal import Decimal

            ## Now handled by background worker
            # img_filepath        =   dt.pdf_to_image(source, source_path)            # 1. Converts initial PDF doc to image, returns image location
            # pdf_filepath        =   dt.image_to_pdf(img_filepath)                   # 2. Converts image to "searchable pdf"
            # doctext, word_coords =  dt.pdf_to_text_coordinates(pdf_filepath)        # 3. Get document text from PDF, then get coordinates of each word
            
            img_filepath = source + ".png"                # TBD:  check this exists
            pdf_filepath = source + ".png.processed.pdf"  # TBD:  check this exists
            doctext, word_coords = doc.text, doc.word_coords
        
            # Compatbility fix.  Data versions have been different so this is a remnant that will be around as long as the next version with Azure replaces this.
            if type(word_coords) == str:
                coords = json.loads(word_coords)
                if type(coords) == list:
                    coords = dict(words = coords)

            elif type(word_coords) == list:
                coords = word_coords[0]
            else:
                coords = word_coords

            ## Convert back to decimal for legacy code -- we use JSON type for widget in backend.
            coords['words'] = [
                {
                    name: Decimal(value) if type(value) == float else value 
                    for name, value in row.items()
                } 
                for row in coords['words']
            ]

            matches             =   dt.get_entity_matches(doctext, coords)      # 4. Extract matches /w coordinates
            hilight_coords      =   dt.image_to_highlighted(matches, pdf_filepath, img_filepath)    
            entities            =   dt.map_entities(pdf_filepath, coords, doctext = doctext, vocabulary = coords)

            self.request.session['import_doc'] = {
                "p":                        token,
                "datetime":                 str(datetime.now()),
                "deal_id":                  self.kwargs['pk'],
                "doc_id":                   self.kwargs['doc_id'],
                "original_document_name":   doc.original_doc_name
            }

            if type(entities) == list and entities[0]:
                for entity in entities:
                    try: 
                        self.request.session['import_doc'][entity['entity_name']] = entity['entity_value']
                    except:
                        print("Could not set entity:", entity)
                        
            highlighted_image   =   f"{doc.original_doc_name}"
            x, y                =   dt.get_image_dimensions(img_filepath)

            return JsonResponse({
                'status':           200, 
                'success':          True, 
                'p':                token,
                'processed_doc':    highlighted_image, 
                'letter_coords':    coords, 
                'hilight_coords':   hilight_coords,
                'image_size':       dict(x = x, y = y),
                'entities':         entities
            })

        return self.render_to_response(data)