import os
import json
import csv
import re
from collections import defaultdict

def find_json_in_text(content):
    """
    Finds and extracts the JSON string from the raw text file content.
    """
    match = re.search(r'm_Script\s*=\s*"(.*)"', content, re.DOTALL)
    if match:
        json_string = match.group(1)
        # Unescape for parsing, but keep the original raw string for replacement.
        processed_string = json_string.replace('\\"', '"')
        processed_string = processed_string.replace('\\r\\n', '\n')
        processed_string = processed_string.lstrip('\ufeff')
        return processed_string
    return None

def reconstruct_string(structure, translations):
    """
    Reconstructs a single string from its structural metadata and translated parts.
    """
    result = ""
    for part in structure:
        if part['type'] == 'text':
            csv_id = part['csv_id']
            result += translations.get(csv_id, f"ERROR_NO_TRANSLATION_FOR_{csv_id}")
        elif part['type'] == 'marker':
            result += part['value']
    return result

def main():
    textos_dir = 'textos'
    output_dir = 'espanol'

    # --- 1. Load Data ---
    csv_filepath = os.path.join(textos_dir, 'text_to_translate.csv')
    metadata_filepath = os.path.join(textos_dir, 'metadata.json')

    translations = {}
    with open(csv_filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # Skip header
        for row in reader:
            translations[row[0]] = row[1]
    print("Loaded translations from CSV.")

    with open(metadata_filepath, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    print("Loaded metadata.")

    # --- 2. Group Metadata by File ---
    files_to_process = defaultdict(list)
    for entry_id, data in metadata.items():
        files_to_process[data['original_file']].append(data)

    print(f"Found {len(files_to_process)} file(s) to process.")
    os.makedirs(output_dir, exist_ok=True)

    # --- 3. Process Each File ---
    for original_filepath, entries in files_to_process.items():
        print(f"\nProcessing file: {original_filepath}")

        with open(original_filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

        modified_content = original_content

        # We parse the clean JSON only to get a reliable map of original English text.
        # The replacement will happen on the raw `original_content` string.
        json_string_clean = find_json_in_text(original_content)
        original_json_data = json.loads(json_string_clean)
        original_texts = {item['ID']: item['English'] for item in original_json_data.get('Data', [])}

        for entry in entries:
            json_id = entry['json_id']

            new_string = reconstruct_string(entry['structure'], translations)
            original_string = original_texts.get(json_id)

            if original_string is None:
                print(f"  - WARNING: Could not find original text for ID {json_id}. Skipping.")
                continue

            # Escape both original and new strings to match the raw file format.
            original_string_escaped = original_string.replace('"', '\\"')
            new_string_escaped = new_string.replace('"', '\\"')

            # Construct the field to search for, including the literal backslashes.
            original_field = f'\\"English\\":\\"{original_string_escaped}\\"'
            new_field = f'\\"English\\":\\"{new_string_escaped}\\"'

            # Perform the replacement on the entire file's content.
            if original_field in modified_content:
                modified_content = modified_content.replace(original_field, new_field, 1)
                print(f'  - Injected text for ID: {json_id}')
            else:
                print(f'  - FAILED to find text for ID: {json_id}')
                print(f'    - Searched for: {repr(original_field)}')

        # --- 4. Save the New File ---
        output_filename = os.path.basename(original_filepath)
        output_filepath = os.path.join(output_dir, output_filename)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"Successfully created translated file: {output_filepath}")

if __name__ == '__main__':
    main()
