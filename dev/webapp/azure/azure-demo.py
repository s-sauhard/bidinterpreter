import time, os
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes


'''
Authenticate
Authenticates your credentials and creates a client.
'''
subscription_key    = "5b522eec6a7a429a86dc3a21ecb3a530"
endpoint            = "https://loihub.cognitiveservices.azure.com/"

# Init client
credentials         = CognitiveServicesCredentials(subscription_key)
client              = ComputerVisionClient(endpoint, credentials)


'''
Read and extract from the image
'''
def pdf_text(filepath):
    # Images PDF with text
    filepath = open(filepath,'rb')

    # Async SDK call that "reads" the image
    response = client.read_in_stream(filepath, raw=True)
    # Don't forget to close the file
    filepath.close()

    # Get ID from returned headers
    operation_location = response.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # SDK call that gets what is read
    while True:
        result = client.get_read_result(operation_id) # get_read_operation_result(operation_id)
        if result.status not in [OperationStatusCodes.not_started, OperationStatusCodes.running]:
            break
        time.sleep(1)
    return result


# PDF convert example
local_file = "/Users/david.yerrington/Projects/bidinterpreter/test.pdf"

'''
Display extracted text and bounding box
'''
# Displays text captured and its bounding box (position in the image)
result = pdf_text(local_file)

print(result.as_dict())
print("result is:", result.status, type(result.status))
if result.status == OperationStatusCodes.succeeded:
    print(result.analyze_result.read_results[0].lines[0])
    # for textResult in result.analyze_result.read_results:
    #     for line in textResult.lines:
            
    #         # print(line.text, type(line.text))
    #         #print(line.bounding_box)
    #     print()
