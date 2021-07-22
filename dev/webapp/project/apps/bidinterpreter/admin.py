from django.contrib import admin
from django.db import models

from django_json_widget.widgets import JSONEditorWidget
from .models import Deal, DealInvite, Bid, BidDoc, BidDocStats
from django.conf import settings

from django import template
from .doctools import DocTools

from decimal import Decimal

# ML loading
import numpy as np
from joblib import dump, load
import nltk

# Register your models here.

admin.site.register(Deal)
admin.site.register(Bid)
# admin.site.register(BidDoc, BidDocAdmin)
admin.site.register(DealInvite)

@admin.register(BidDoc)
class BidDocAdmin(admin.ModelAdmin):
    list_display = ('status', 'deal', 'original_doc_name')
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(BidDocStats)
class BidDocStatsAdmin(admin.ModelAdmin):
    change_form_template = "bidinterpreter/admin/biddocstats.html"

    search_fields = ['original_doc_name']
    list_display = ['original_doc_name_bid', 'start', 'pytesseract_processing_time']

    def get_sentence_predictions(self, text):

        sentences   = nltk.sent_tokenize(text)
        class_names = ['closing', 'dd', 'deposit', 'none', 'purchase_price']

        # load model
        model   = load('models/sentence_model.joblib')
        y_hat_proba = model.predict_proba(sentences).round(3).tolist()
        y_hat       = model.predict(sentences).tolist()

        # return sentences, y_hat -- forgive the complex comprehension it's just easier to write
        return [
            {
                "sentence":  row[0], 
                "predicted": class_names[row[2]],
                "y_hat": {
                    item[0]: item[1] for item in list(zip(class_names, row[1]))
                }
            } for row in zip(sentences, y_hat_proba, y_hat)
        ]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        
        dt      = DocTools(django_settings = settings)
        stat    = BidDocStats.objects.get(pk=object_id)

        if stat.biddoc == None:
            return super().change_view(
                request, object_id, form_url, extra_context=extra_context,
            )
 
        doc_name = stat.biddoc.original_doc_name.split('/')[-1::][0]
        
        img_filepath = f"{stat.biddoc.deal_id}/{doc_name}.png"
        pdf_filepath = f"{stat.biddoc.deal_id}/{doc_name}.png.processed.pdf"
        doctext, word_coords = stat.biddoc.text, stat.biddoc.word_coords

        print("img_filepath", img_filepath)
        print('pdf_filepath', pdf_filepath)

        ## Convert back to decimal for legacy code -- we use JSON type for widget in backend.
        word_coords = word_coords = [{name: Decimal(value) if type(value) == float else value for name, value in row.items()} for row in word_coords[0]['words']]

        matches             =   dt.get_entity_matches(doctext, word_coords)      # 4. Extract matches /w coordinates
        hilight_coords      =   dt.image_to_highlighted(matches, pdf_filepath, img_filepath)    
        entities            =   dt.map_entities(pdf_filepath, word_coords, doctext = doctext, vocabulary = word_coords)

        extra_context['entities'] = entities
        extra_context['sentences'] = self.get_sentence_predictions(doctext)
        
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def original_doc_name(self, row):
        return row.original_doc_name.split("/")[-1:]

    def original_doc_name_bid(self, row):
        return row.original_doc_name.split("/")[-1:]

    def pytesseract_processing_time(self, row):
        if row.end and row.start:
            return row.end - row.start
        return 

    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }

