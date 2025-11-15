import json
import re


# ------------------------------------------------------
# File paths
# ------------------------------------------------------
raw_text_file = r"C:\Users\RamyaSandhiveeran\Documents\PYTHON_SELENIUM\DataSet\IN_DataSet\IN_Raw_Text\Owen_Raw_Text.txt"
output_txt_file = r"C:\Users\RamyaSandhiveeran\Documents\PYTHON_SELENIUM\DataSet\IN_DataSet\IN_Output\Owen_Output.txt"
dataset_json_file = r"C:\Users\RamyaSandhiveeran\Documents\PYTHON_SELENIUM\DataSet\IN_DataSet\IN_Json\Owen.json"


# ------------------------------------------------------
# Function to clean text
# ------------------------------------------------------
def clean(text: str) -> str:
    """Convert multi-line raw text into a single line string."""
    return ' '.join(text.strip().splitlines())


# ------------------------------------------------------
# 1️⃣ Extract raw text records
# ------------------------------------------------------
def extract_raw_texts():
    with open(raw_text_file, "r", encoding="utf-8") as f:
        content = f.read()


    # Split by start and end markers
    pattern = re.compile(
        r"Property Information:(.*?)(?:Due Dates:\s*May 12, 2025\s*November 10, 2025)",
        re.DOTALL
    )
    raw_records = pattern.findall(content)
    print(f"Found {len(raw_records)} raw text records.")
    return raw_records


# ------------------------------------------------------
# 2️⃣ Extract output records
# ------------------------------------------------------
def extract_output_records():
    with open(output_txt_file, "r", encoding="utf-8") as f:
        content = f.read()


    # Split each record by --- Record X ---
    records = re.split(r"--- Record \d+ ---", content)
    parsed_outputs = []


    for block in records:
        block = block.strip()
        if not block or block.startswith("--------------------------------------------------------------------------------"):
            continue
        # Extract only JSON content
        json_match = re.search(r"\{[\s\S]*\}", block)
        if json_match:
            json_text = json_match.group(0)
            try:
                parsed_outputs.append(json.loads(json_text))
            except json.JSONDecodeError as e:
                print(f"JSON parsing error in one record: {e}")
    print(f"Found {len(parsed_outputs)} output records.")
    return parsed_outputs


# ------------------------------------------------------
# 3️⃣ Combine raw text + output into dataset
# ------------------------------------------------------
def build_dataset():
    raw_records = extract_raw_texts()
    output_records = extract_output_records()


    dataset = []
    for i, (raw, output) in enumerate(zip(raw_records, output_records), start=1):
        # Extract taxYear value from output JSON
        tax_year = ""
        try:
            tax_year = output["parcels"][0].get("taxYear", "")
        except (KeyError, IndexError, TypeError):
            pass


        # Rebuild "output" structure by inserting taxYear after "delinquentNotes"
        if "parcels" in output and isinstance(output["parcels"], list):
            for parcel in output["parcels"]:
                # Move taxYear key after delinquentNotes
                if "taxYear" in parcel:
                    # Temporarily store and remove
                    ty = parcel.pop("taxYear")
                    # Build new ordered dict-like structure
                    new_parcel = {}
                    for key, value in parcel.items():
                        new_parcel[key] = value
                        if key == "delinquentNotes":
                            new_parcel["taxYear"] = ty
                    parcel.clear()
                    parcel.update(new_parcel)


        record = {
            "instruction": "",
            "input": clean(raw),
            "output": output
        }
        dataset.append(record)


    print(f"Created dataset with {len(dataset)} records.")
    return dataset


# ------------------------------------------------------
# 4️⃣ Save final dataset JSON
# ------------------------------------------------------
def save_dataset(dataset):
    with open(dataset_json_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Dataset saved to: {dataset_json_file}")


# ------------------------------------------------------
# Run
# ------------------------------------------------------
if __name__ == "__main__":
    dataset = build_dataset()
    save_dataset(dataset)
