import json
import csv

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
                    # Withdrawal amounts should be negative
                    if props.get("table_item/transaction_withdrawal") is not None:
                        amt_val = -abs(amt_val)
                    transactions.append([date, description, amt_val])
                except ValueError:
                    continue
    return transactions

def main():
    input_filename = "document_ai_response.json"
    output_filename = "extracted_transactions.csv"
    
    with open(input_filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        entities = data.get("entities", [])
        transactions = extract_transactions_from_entities(entities)
    
    with open(output_filename, "w", newline='', encoding="utf-8") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(["Date", "Description", "Amount"])
        writer.writerows(transactions)
    
    print(f"Extracted {len(transactions)} transactions to {output_filename}")

if __name__ == "__main__":
    main()
