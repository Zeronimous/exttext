import os
import json
import csv
import re
from collections import defaultdict

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

        # Reconstruct all translated strings for the current file
        reconstructed_strings = {}
        for entry in entries:
            json_id = entry['json_id']
            reconstructed_strings[json_id] = reconstruct_string(entry['structure'], translations)

        # We must operate on the raw m_Script block
        script_match = re.search(r'(m_Script\s*=\s*")(.*)(")', original_content, re.DOTALL)
        if not script_match:
            print(f"  - WARNING: Could not find m_Script block in {original_filepath}. Skipping.")
            continue

        prefix = script_match.group(1) # 'm_Script = "'
        script_content = script_match.group(2) # The actual content with escaped quotes
        suffix = script_match.group(3) # '"'

        # This is the key: replace within the raw script content string
        for json_id, new_text in reconstructed_strings.items():
            # Escape the new text for injection
            new_text_escaped = new_text.replace('"', '\\"')

            # Build a regex that finds the "English" value belonging to a specific ID
            # It looks for "ID":"the_id", anything, "English":" and captures the value
            pattern = re.compile(
                f'(\\"ID\\"\\s*:\\s*\\"{json_id}\\".*?\\"English\\"\\s*:\\s*\\")([^\\"]*)(\\")'
            )

            # We perform the substitution on the script_content, not the whole file
            script_content, num_replacements = pattern.subn(
                f'\\g<1>{new_text_escaped}\\g<3>',
                script_content,
                count=1
            )

            if num_replacements > 0:
                print(f'  - Injected text for ID: {json_id}')
            else:
                print(f'  - FAILED to find text for ID: {json_id}')

        # Rebuild the full file content
        new_script_block = prefix + script_content + suffix
        modified_content = original_content.replace(script_match.group(0), new_script_block)

        # --- 4. Save the New File ---
        output_filename = os.path.basename(original_filepath)
        output_filepath = os.path.join(output_dir, output_filename)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"Successfully created translated file: {output_filepath}")

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

if __name__ == '__main__':
    main()
