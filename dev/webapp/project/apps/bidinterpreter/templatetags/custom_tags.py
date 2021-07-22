from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from decimal import Decimal
import json

register = template.Library()

@register.filter
def remove_path(filepath):
    return filepath.split('/')[-1:][0]

@register.simple_tag
def elapsed(end, start):
    if end and start:
        return end - start
    return None

@register.simple_tag
def azure_wordcount(result):
    entities = 0
    for page in result:
        for line in page.get('lines'):
            entities += len(line['words'])
    return entities

@register.simple_tag
def get_file(biddoc):
    if biddoc == None:
        return None
    return f"{settings.MEDIA_URL}{biddoc.deal_id}/{biddoc.original_doc_name}"

"""
{'text': 'IEC', 'words': [{'text': 'IEC', 'confidence': 0.984, 'bounding_box': [1.3433, 1.3033, 1.9967, 1.3033, 1.9967, 1.5833, 1.3433, 1.5833]}], 'bounding_box': [1.3433, 1.3067, 2.03, 1.3033, 2.03, 1.5833, 1.3533, 1.5833]}
"""

@register.filter
def format_azure_results(results):
    lines = ""
    for line in results:
        lines += f"{line['text']}\n"

    return lines

@register.filter
def to_json(value):

    for index, row in enumerate(value):
        for k, v in row.items():
            try: 
                if type(v) == Decimal:
                    value[index][k] = float(v)
            except Exception as error:
                print(f'Error with {v} is:', error)
    return mark_safe(json.dumps(value))


@register.filter(name='addclass')
def addclass(value, arg):
    return value.as_widget(attrs={'class': arg})