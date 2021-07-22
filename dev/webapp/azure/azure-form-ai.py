import os
from azure.core.exceptions import ResourceNotFoundError
from azure.ai.formrecognizer import FormRecognizerClient
from azure.ai.formrecognizer import FormTrainingClient
from azure.core.credentials import AzureKeyCredential

subscription_key    = "2fc870f78ad54a1b9eba2d3f66785340"
endpoint            = "https://loihub-form.cognitiveservices.azure.com/"


form_recognizer_client = FormRecognizerClient(endpoint, AzureKeyCredential(subscription_key))
# form_training_client = FormTrainingClient(endpoint, AzureKeyCredential(subscription_key))



formUrl = "https://raw.githubusercontent.com/Azure/azure-sdk-for-python/master/sdk/formrecognizer/azure-ai-formrecognizer/tests/sample_forms/forms/Form_1.jpg"

# poller = form_recognizer_client.begin_recognize_content_from_url(formUrl)

local_file = "/Users/david.yerrington/Projects/bidinterpreter/test.pdf"

# Images PDF with text
filepath = open(local_file,'rb')

# Async SDK call that "reads" the image
response = form_recognizer_client.begin_recognize_content(filepath)
# Don't forget to close the file
filepath.close()


page = response.result()
print(page[0].lines[0])

# table = page[0].tables[0] # page 1, table 1
# print("Table found on page {}:".format(table.page_number))
# for cell in table.cells:
#     print("Cell text: {}".format(cell.text))
#     print("Location: {}".format(cell.bounding_box))
#     print("Confidence score: {}\n".format(cell.confidence))