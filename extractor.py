import os
import json
import csv
import re
import codecs

def find_and_parse_json(content):
    """
    Finds the m_Script block and parses its content using the appropriate escape handling.
    """
    match = re.search(r'm_Script\s*=\s*"(.*)"', content, re.DOTALL)
    if not match:
        return None

    json_string_escaped = match.group(1)

    # The 'unicode_escape' codec is designed to handle strings with Python-style
    # backslash escapes. This is the robust way to handle the file format.
    # We must strip the BOM before decoding.
    bom = '\ufeff'
    if json_string_escaped.startswith(bom):
        json_string_escaped = json_string_escaped[len(bom):]

    # This will correctly interpret \\" as " and \\r\\n as a newline.
    decoded_string = codecs.decode(json_string_escaped, 'unicode_escape')

    try:
        return json.loads(decoded_string)
    except json.JSONDecodeError as e:
        print(f"  - Error decoding JSON: {e}")
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

    split_pattern = r'(<[^>]+>|{[^}]+})'
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

        data = find_and_parse_json(content)
        if not data:
            print(f"  - No valid JSON found in {filename}. Skipping.")
            continue

        for item in data.get('Data', []):
            json_id = item.get('ID')
            english_text = item.get('English')

            if not json_id or not english_text:
                continue

            # New rule: Check if the text is surrounded by quotes and strip them.
            is_quoted = False
            if english_text.startswith('"') and english_text.endswith('"'):
                english_text = english_text[1:-1]
                is_quoted = True

            if re.fullmatch(ignore_pattern, english_text):
                print(f"  - Ignoring entry {json_id} (placeholder only).")
                continue

            file_id = entry_counter
            structure_metadata = []

            parts = re.split(split_pattern, english_text)
            segment_index = 1

            for part in parts:
                if not part:
                    continue

                if re.fullmatch(split_pattern, part):
                    structure_metadata.append({"type": "marker", "value": part})
                else:
                    segment_index = process_text_segment(part, file_id, segment_index, csv_rows, structure_metadata)

            if structure_metadata:
                metadata[file_id] = {
                    "original_file": filepath,
                    "json_id": json_id,
                    "is_quoted": is_quoted,
                    "structure": structure_metadata
                }
                entry_counter += 1

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
