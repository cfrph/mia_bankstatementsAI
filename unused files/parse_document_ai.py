import json

def split_and_save_json(data, num_parts=20):
    entities = data.get("entities", [])
    chunk_size = len(entities) // num_parts + 1

    for i in range(num_parts):
        chunk_entities = entities[i*chunk_size:(i+1)*chunk_size]
        chunk_data = data.copy()
        chunk_data["entities"] = chunk_entities

        with open(f"document_ai_response_part{i+1}.json", "w", encoding="utf-8") as out_f:
            json.dump(chunk_data, out_f, ensure_ascii=False, indent=2)
        print(f"Saved document_ai_response_part{i+1}.json with {len(chunk_entities)} entities.")

# Usage example:
with open("document_ai_response.json", "r", encoding="utf-8") as f:
    full_data = json.load(f)

split_and_save_json(full_data, num_parts=20)
