import json
import csv

from google.cloud import documentai_v1 as documentai

# Extraction function adapted from your previous work
def extract_transactions_from_entities(entities):
    transactions = []
    for entity in entities:
        if entity.get("type_") == "table_item":
            props = {p["type_"]: p.get("mention_text", "") for p in entity.get("properties", [])}
            date = props.get("table_item/transaction_withdrawal_date") or props.get("table_item/transaction_deposit_date", "")
            description = props.get("table_item/transaction_withdrawal_description") or props.get("table_item/transaction_deposit_description", "")
            amount = props.get("table_item/transaction_withdrawal") or props.get("table_item/transaction_deposit", "")
            if date and description and amount:
                amt_clean = amount.replace('$', '').replace(',', '').strip()
                try:
                    amt_val = float(amt_clean)
                    # Withdrawals marked negative
                    if props.get("table_item/transaction_withdrawal") is not None:
                        amt_val = -abs(amt_val)
                    transactions.append([date, description, amt_val])
                except ValueError:
                    continue
    return transactions

# Placeholder for your mapping dicts - add mappings later as needed
debit_mapping = {}
credit_mapping = {}

def match_mapping(description, mapping_dict):
    for k in mapping_dict:
        if k.lower() in description.lower():
            return mapping_dict[k]
    return ("UNMAPPED", "")

def process_tcb_json(json_data, journal_start, deposit_start):
    if not json_data:
        # Defensive: return empty lists if JSON is None or invalid
        return [], [], []

    # Safely get entities list or empty
    entities = json_data.get("entities", [])
    transactions = extract_transactions_from_entities(entities)

    debits, credits, unmapped = [], [], []
    journal_num = int(journal_start)
    deposit_num = int(deposit_start)

    for date, description, amount in transactions:
        if amount < 0:
            short_desc, acct = match_mapping(description, debit_mapping)
            row = [journal_num, date, short_desc, description, amount, acct]
            debits.append(row)
            journal_num += 1
            if short_desc == "UNMAPPED":
                unmapped.append(row)
        else:
            short_desc, acct = match_mapping(description, credit_mapping)
            row = [deposit_num, date, short_desc, description, amount, acct]
            credits.append(row)
            deposit_num += 1
            if short_desc == "UNMAPPED":
                unmapped.append(row)

    return debits, credits, unmapped

def save_csv(filename, rows, header):
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} entries to {filename}")

def process_pdf(pdf_bytes):
    try:
        client = documentai.DocumentProcessorServiceClient()

        project_id = "YOUR_PROJECT_ID"  # Replace with your GCP project ID
        location = "YOUR_PROCESSOR_LOCATION"  # e.g., "us"
        processor_id = "YOUR_PROCESSOR_ID"  # Your Document AI processor ID

        name = client.processor_path(project_id, location, processor_id)

        request = documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(
                content=pdf_bytes,
                mime_type="application/pdf"
            )
        )

        result = client.process_document(request=request)
        # The returned result is of proto type; convert to JSON dict
        document_json = json.loads(result.document.to_json())
        return document_json
    except Exception as e:
        # Log or handle exception as needed
        print(f"Error processing document in Document AI: {e}")
        return None

if __name__ == "__main__":
    # Example local test with a saved JSON response
    with open("document_ai_response.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    journal_start = input("Enter journal start number: ")
    deposit_start = input("Enter deposit start number: ")
    debits, credits, unmapped = process_tcb_json(data, journal_start, deposit_start)
    save_csv("tcb_debits.csv", debits, ["Journal#", "Date", "Short Desc", "Full Desc", "Amount", "Account#"])
    save_csv("tcb_credits.csv", credits, ["Deposit#", "Date", "Short Desc", "Full Desc", "Amount", "Account#"])
    if unmapped:
        save_csv("tcb_unmapped.csv", unmapped, ["Entry#", "Date", "Short Desc", "Full Desc", "Amount", "Account#"])
