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

        # Isolate the content of the m_Script block to perform replacements on.
        script_match = re.search(r'(m_Script\s*=\s*")(.*)(")', original_content, re.DOTALL)
        if not script_match:
            print(f"  - WARNING: Could not find m_Script block in {original_filepath}. Skipping.")
            continue

        prefix = script_match.group(1)
        script_content = script_match.group(2)
        suffix = script_match.group(3)

        # Reconstruct all translated strings for the current file
        reconstructed_strings = {}
        for entry in entries:
            json_id = entry['json_id']
            reconstructed_strings[json_id] = reconstruct_string(entry['structure'], translations)

        # Replace each entry within the raw script content string
        for entry_metadata in entries:
            json_id = entry_metadata['json_id']
            new_text = reconstructed_strings[json_id]

            # Format the final text based on whether it was originally quoted
            if entry_metadata.get('is_quoted', False):
                # Escape any quotes inside the translated text first
                escaped_inner_text = new_text.replace('"', '\\"')
                # Add the surrounding escaped quotes
                final_text_for_injection = f'\\"{escaped_inner_text}\\"'
            else:
                # Just escape the text as usual
                final_text_for_injection = new_text.replace('"', '\\"')

            # This regex finds the "English" field associated with a specific "ID".
            # It now correctly includes the opening brace of the JSON object.
            pattern = re.compile(
                # Group 1: The part before the value, from the opening brace and ID to the opening quote of the English text.
                # Note the '{{' to escape the brace for the f-string.
                f'({{\\"ID\\"\\s*:\\s*\\"{re.escape(json_id)}\\".*?\\"English\\"\\s*:\\s*\\")'
                # Group 2: The value itself. This pattern matches a string that can contain escaped quotes.
                r'((?:\\\\"|[^"])*)'
                # Group 3: The closing quote of the value.
                r'(\\")'
            )

            # The replacement string in re.sub also uses backslashes for backreferences.
            # To insert a literal backslash, it must be escaped.
            final_text_for_sub = final_text_for_injection.replace('\\', '\\\\')

            replacement_string = f'\\g<1>{final_text_for_sub}\\g<3>'
            script_content, num_replacements = pattern.subn(replacement_string, script_content, count=1)

            if num_replacements > 0:
                print(f'  - Injected text for ID: {json_id}')
            else:
                print(f'  - FAILED to find text for ID: {json_id}')

        # Rebuild the full file content with the modified script block
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
