from google.cloud import documentai_v1 as documentai
from google.cloud.documentai_v1 import types
import os

# Set your Google Cloud project variables
PROJECT_ID = "linear-poet-477701-q6"
LOCATION = "us"  # processor location
PROCESSOR_ID = "e8c76bc446687873"

# Path to the PDF file to test
FILE_PATH = r"C:\Users\cfrph\Documents\MS in Data Science\Times_Square_Optical_Files\Flask App Multiledger Import 2025\gc_bank_statement_ai\Times Square Optical-STATEMENT-09-30-2025-e771519b-d4db-4264-8a3c-996b558453a2.pdf"

def process_document():
    # Instantiates a client
    client = documentai.DocumentProcessorServiceClient()

    # The full resource name of the processor
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

    # Read the file into memory
    with open(FILE_PATH, "rb") as file:
        file_content = file.read()

    document = {
        "content": file_content,
        "mime_type": "application/pdf"
    }

    request = {
        "name": name,
        "raw_document": document
    }

    # Use the Document AI client to process the document
    response = client.process_document(request=request)

    # Get the document object from the response
    document = response.document

    # Print the document text (optional)
    print("Document Text:")
    print(document.text)

    # Print the full JSON response for inspection
    print("\nFull Document AI Response:")
    print(response)

if __name__ == "__main__":
    process_document()
