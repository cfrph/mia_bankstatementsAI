import os
import json
import csv
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from google.protobuf.json_format import MessageToDict

# --- Cloud and Processor Config ---
GCP_PROJECT_ID = "linear-poet-477701-q6"
GCP_PROCESSOR_ID = "6df7b78a3654d182"
GCP_LOCATION = "us"

# --- Account Mappings ---
credit_account_map = {
    "MERCHANT BANKCD DEPOSIT ACH ENTRY MEMO POSTED TODAY": "DEP MERCH BANK CCD MAIN",
    "SYNCHRONY BANK MTOT DEP ACH ENTRY MEMO POSTED TODAY": "SYNCHRONY BANK CCD",
    "DEPOSIT MERCHANT BANKCD CCD": "DEP MERCH BANK CCD MAIN",
    "REGULAR DEPOSIT": "REGULAR DEPOSIT",
    "CIGNA": "FAA - CIGNA CCD",
    "EYEMED VISION CCD": "EYEMED VISION CCD",
    "ESSILOR": "ESSILOR SAFETY CCD",
    "EYETOPIA": "REIMB EYETOPIA CCD",
    "FAA ADMIN CCD": "FAA ADMIN CCD",
    "MTOT DEP SYNCHRONY BANK CCD": "SYNCHRONY BANK CCD",
    "HCCLAIMPMT SUPERIOR VISION CCD": "SUPERIOR VISION CCD",
    "HCCLAIMPMT UHC SPECTERA VSN CCD": "UHC SPECTERA VISION",
    "DAVIS VISION CCD": "DAVIS VISION CCD",
    "1010877933 FAA - AETNA CCD": "FAA - AETNA CCD",
    "FSL ADMIN FAA CCD": "FSL ADMIN FAA CCD",
}

debit_account_map = {
    "USATAXPYMT IRS CCD": "2060",
    "USA TAX PYMT IRS CCD": "2060",
    "USA TAX PYMT IRS": "2060",
    "AUTOPAYBUS CHASE CREDIT CRD PPD": "2130",
    "CRCARDPMT CAPITAL ONE CCD": "2130",
    "CAPITAL ONE VISA PMT": "2130",
    "CHASE VISA PMT 7772": "2135",
    "CHASE VISA PMT 3506": "2136",
    "DISCOUNT MERCHANT BANKCD CCD": "6460",
    "DISCT MERCH BANK CCD": "6460",
    "MERCH BANK DISCT ACH": "6460",
    "FEE MERCHANT BANKCD CCD": "6460",
    "FEE MERCH BANK CCD": "6460",
    "MERCH BANK FEE ACH": "6460",
    "INTERCHNG MERCHANT BANKCD CCD": "6460",
    "INTERCHNG MERCH BANK CCD": "6460",
    "INTERCHNG MERCH BANK": "6460",
    "MERCH BANK INTERCHNG ACH": "6460",
    "WEB PAY PECAA BUYING GRP": "5000",
    "PECAA BUYING GRP": "5000",
    "ADT ALARM": "7475",
    "EVERON ALARM": "7475",
    "IPAY BILL PAY": "6200",
    "MBFS.COM MERCEDES LEASE": "7260",
    "TX WORKFORCE COMM": "2070",
}

def process_pdf(pdf_bytes):
    try:
        client_options = ClientOptions(api_endpoint=f"{GCP_LOCATION}-documentai.googleapis.com")
        client = documentai.DocumentProcessorServiceClient(client_options=client_options)

        name = client.processor_path(GCP_PROJECT_ID, GCP_LOCATION, GCP_PROCESSOR_ID)

        request = documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(content=pdf_bytes, mime_type="application/pdf")
        )

        result = client.process_document(request=request)
        document_dict = MessageToDict(result.document._pb)
        return document_dict
    except Exception as e:
        print(f"Error processing document with Document AI: {e}")
        return None

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
                    if props.get("table_item/transaction_withdrawal") is not None:
                        amt_val = -abs(amt_val)
                    transactions.append([date, description, amt_val])
                except ValueError:
                    continue
    return transactions

def match_mapping(description, mapping_dict):
    for k in mapping_dict:
        if k.lower() in description.lower():
            return mapping_dict[k]
    return ("UNMAPPED", "")

def process_tcb_json(json_data, journal_start, deposit_start):
    if not json_data:
        return [], [], []

    entities = json_data.get("entities", [])
    transactions = extract_transactions_from_entities(entities)

    debits, credits, unmapped = [], [], []
    journal_num = int(journal_start)
    deposit_num = int(deposit_start)

    for date, description, amount in transactions:
        if amount < 0:
            short_desc, acct = match_mapping(description, debit_account_map)
            row = [journal_num, date, short_desc, description, amount, acct]
            debits.append(row)
            journal_num += 1
            if short_desc == "UNMAPPED":
                unmapped.append(row)
        else:
            short_desc, acct = match_mapping(description, credit_account_map)
            row = [deposit_num, date, short_desc, description, amount, acct]
            credits.append(row)
            deposit_num += 1
            if short_desc == "UNMAPPED":
                unmapped.append(row)

    return debits, credits, unmapped