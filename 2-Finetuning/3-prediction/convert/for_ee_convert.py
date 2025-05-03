import csv
import json
import os

def convert_csv_to_jsonl(csv_filepath, jsonl_filepath):
    """
    Reads a CSV file, extracts the 'rich_text' column, and writes it to a JSONL file
    in a format suitable for LLM inference.

    Args:
        csv_filepath (str): The path to the input CSV file.
        jsonl_filepath (str): The path where the output JSONL file will be saved.
    """
    # Check if the input CSV file exists
    if not os.path.exists(csv_filepath):
        print(f"Error: Input CSV file not found at {csv_filepath}")
        return

    print(f"Reading from {csv_filepath} and writing to {jsonl_filepath}")

    try:
        # Open the CSV file for reading
        with open(csv_filepath, mode='r', encoding='utf-8') as infile:
            # Use DictReader to read rows as dictionaries
            reader = csv.DictReader(infile)

            # Check if 'rich_text' column exists
            if 'rich_text' not in reader.fieldnames:
                print(f"Error: 'rich_text' column not found in the CSV file.")
                print(f"Available columns: {', '.join(reader.fieldnames)}")
                return

            # Open the JSONL file for writing
            with open(jsonl_filepath, mode='w', encoding='utf-8') as outfile:
                # Iterate through each row in the CSV
                for i, row in enumerate(reader):
                    # Extract the content from the 'rich_text' column
                    rich_text_content = row.get('rich_text', '') # Use .get to handle potential missing keys gracefully

                    # Create the dictionary in the desired JSONL format
                    jsonl_entry = {
                        "instruction": "请从以下文本中抽取所有事件，包含事件类型、触发词和论元角色及其内容。",
                        "input": rich_text_content
                    }

                    # Write the dictionary as a JSON string followed by a newline
                    outfile.write(json.dumps(jsonl_entry, ensure_ascii=False) + '\n')

                    # Optional: Print progress
                    if (i + 1) % 100 == 0:
                        print(f"Processed {i + 1} rows...")

        print(f"Successfully converted {csv_filepath} to {jsonl_filepath}")

    except FileNotFoundError:
        print(f"Error: Could not open file {csv_filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    input_path = "sina_data_results.csv"    # 原始event格式路径
    output_path = "for_ee_predict.jsonl" # 转换后输出路径
    convert_csv_to_jsonl(input_path, output_path)
