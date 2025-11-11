from google.cloud import documentai_v1 as documentai
import json

PROJECT_ID = "linear-poet-477701-q6"
LOCATION = "us"
PROCESSOR_ID = "e8c76bc446687873"
FILE_PATH = r"C:\Users\cfrph\Documents\MS in Data Science\Times_Square_Optical_Files\Flask App Multiledger Import 2025\gc_bank_statement_ai\Times Square Optical-STATEMENT-09-30-2025-e771519b-d4db-4264-8a3c-996b558453a2.pdf"

def split_and_save_json(data, num_parts=20):
    entities = data.get("entities", [])
    chunk_size = (len(entities) + num_parts - 1) // num_parts  # Ceiling division

    for i in range(num_parts):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        chunk_entities = entities[start:end]
        chunk_data = data.copy()
        chunk_data["entities"] = chunk_entities

        filename = f"document_ai_response_part{i+1}.json"
        with open(filename, "w", encoding="utf-8") as out_f:
            json.dump(chunk_data, out_f, ensure_ascii=False, indent=2)
        print(f"Saved {filename} with {len(chunk_entities)} entities.")

def process_and_save_response():
    client = documentai.DocumentProcessorServiceClient()

    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

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

    response = client.process_document(request=request)
    response_dict = documentai.Document.to_dict(response.document)

    # Save the full response JSON
    with open("document_ai_response.json", "w", encoding="utf-8") as f:
        json.dump(response_dict, f, ensure_ascii=False, indent=2)
    print("Saved full Document AI JSON as document_ai_response.json.")

    # Split into 20 parts
    split_and_save_json(response_dict, num_parts=20)

if __name__ == "__main__":
    process_and_save_response()
