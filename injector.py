import os
import json
import csv
import re
from collections import defaultdict

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
    output_dir = 'espanol' # Use ASCII-compatible name

    # --- 1. Load Data ---
    csv_filepath = os.path.join(textos_dir, 'text_to_translate.csv')
    metadata_filepath = os.path.join(textos_dir, 'metadata.json')

    # Create a dummy translated file for testing purposes.
    # In a real scenario, the user would have translated this file.
    # This dictionary will hold the final translations.
    translations = {}
    with open(csv_filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader) # Skip header
        for row in reader:
            csv_id, text = row
            translations[csv_id] = text # Use the text directly from the CSV
    print("Loaded translations from CSV.")

    with open(metadata_filepath, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    print("Loaded metadata.")

    # --- 2. Group Metadata by File ---
    files_to_process = defaultdict(list)
    for entry_id, data in metadata.items():
        files_to_process[data['original_file']].append(data)

    print(f"Found {len(files_to_process)} file(s) to process.")

    # --- 3. Process Each File ---
    os.makedirs(output_dir, exist_ok=True)

    for original_filepath, entries in files_to_process.items():
        print(f"\nProcessing file: {original_filepath}")

        with open(original_filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

        modified_content = original_content

        # We need the original JSON data to find the text to replace
        json_string_raw = re.search(r'm_Script\s*=\s*"(.*)"', original_content, re.DOTALL).group(1)
        json_string_clean = json_string_raw.replace('\\"', '"').replace('\\r\\n', '\n').lstrip('\ufeff')
        original_json_data = json.loads(json_string_clean)

        # Create a map of ID -> English text for easy lookup
        original_texts = {item['ID']: item['English'] for item in original_json_data.get('Data', [])}

        for entry in entries:
            json_id = entry['json_id']

            # Reconstruct the new, translated string
            new_string = reconstruct_string(entry['structure'], translations)

            # Get the original string to be replaced
            original_string = original_texts.get(json_id)

            if original_string is None:
                print(f"  - WARNING: Could not find original text for ID {json_id} in file. Skipping.")
                continue

            # To ensure the replacement works on the raw text, both the original and new strings
            # must be escaped in the same way the source file formats them (e.g., with \").
            original_string_escaped = original_string.replace('"', '\\"')
            new_string_escaped = new_string.replace('"', '\\"')

            # Construct the full "English":"text" part for replacement
            # We need to match the literal backslashes present in the raw file content.
            original_field = f'\\"English\\":\\"{original_string_escaped}\\"'
            new_field = f'\\"English\\":\\"{new_string_escaped}\\"'

            # Perform the replacement on the content
            modified_content = modified_content.replace(original_field, new_field, 1)
            print(f'  - Injected text for ID: {json_id}')


        # --- 4. Save the New File ---
        output_filename = os.path.basename(original_filepath)
        output_filepath = os.path.join(output_dir, output_filename)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        print(f"Successfully created translated file: {output_filepath}")

if __name__ == '__main__':
    main()
