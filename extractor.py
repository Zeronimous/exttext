import os
import json
import csv
import re

def find_json_in_text(content):
    """
    Finds and extracts the JSON string from the raw text file content.
    The content is expected to have a line like: 1 string m_Script = "{\"Key\": \"Value\"}"
    """
    match = re.search(r'm_Script\s*=\s*"(.*)"', content, re.DOTALL)
    if match:
        json_string = match.group(1)
        # The string from the file has escaped quotes (\") and escaped newlines (\\r\\n).
        # We need to unescape these before parsing with the json library.
        processed_string = json_string.replace('\\"', '"')
        processed_string = processed_string.replace('\\r\\n', '\n')
        processed_string = processed_string.lstrip('\ufeff') # Strip BOM
        return processed_string
    return None

def process_text_segment(text, file_id, segment_index, csv_rows, structure_metadata):
    """
    Adds a text segment to the CSV rows and metadata if it's not empty.
    """
    if text and not text.isspace():
        csv_id = f"{file_id}_{segment_index}"
        csv_rows.append([csv_id, text])
        structure_metadata.append({"type": "text", "csv_id": csv_id})
        return segment_index + 1
    return segment_index

def main():
    input_dir = 'ingles'
    output_dir = 'textos'

    csv_rows = [['ID', 'Text']]
    metadata = {}
    entry_counter = 1

    # Regex to split by markers and placeholders, keeping them
    # Captures: <TAG>, </TAG>, <TAG=...>, {placeholder}, {/placeholder}
    split_pattern = r'(<[^>]+>|{[^}]+})'

    # Regex to check for placeholder-only strings to ignore
    ignore_pattern = r'^{[^}]+}$'

    os.makedirs(output_dir, exist_ok=True)
    print(f"Starting extraction from '{input_dir}'...")

    for filename in os.listdir(input_dir):
        if not filename.endswith('.txt'):
            continue

        filepath = os.path.join(input_dir, filename)
        print(f"Processing file: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        json_string = find_json_in_text(content)
        if not json_string:
            print(f"  - No JSON content found in {filename}. Skipping.")
            continue

        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"  - Error decoding JSON from {filename}: {e}")
            continue

        for item in data.get('Data', []):
            json_id = item.get('ID')
            english_text = item.get('English')

            if not json_id or not english_text:
                continue

            # Rule: Exclude if the text is just a single placeholder like {sigh1}
            if re.fullmatch(ignore_pattern, english_text):
                print(f"  - Ignoring entry {json_id} (placeholder only).")
                continue

            file_id = entry_counter
            structure_metadata = []

            # Split the text by the markers
            parts = re.split(split_pattern, english_text)
            segment_index = 1

            for part in parts:
                if not part:  # re.split can produce empty strings
                    continue

                # Check if the part is a marker/placeholder or regular text
                if re.fullmatch(split_pattern, part):
                    structure_metadata.append({"type": "marker", "value": part})
                else:
                    # This is a text segment
                    segment_index = process_text_segment(part, file_id, segment_index, csv_rows, structure_metadata)

            if structure_metadata:
                metadata[file_id] = {
                    "original_file": filepath,
                    "json_id": json_id,
                    "structure": structure_metadata
                }
                entry_counter += 1

    # Write the results to files
    csv_filepath = os.path.join(output_dir, 'text_to_translate.csv')
    with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)
    print(f"\nSuccessfully created CSV file at: {csv_filepath}")

    metadata_filepath = os.path.join(output_dir, 'metadata.json')
    with open(metadata_filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
    print(f"Successfully created metadata file at: {metadata_filepath}")

if __name__ == '__main__':
    main()
