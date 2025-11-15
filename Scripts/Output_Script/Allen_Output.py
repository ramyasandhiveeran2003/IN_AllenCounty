import json
import re
from datetime import datetime, timedelta


# ------------------------------
# File paths
# ------------------------------
input_file = r"C:\Users\RamyaSandhiveeran\Documents\PYTHON_SELENIUM\DataSet\IN_DataSet\IN_Raw_Text\Owen_Raw_Text.txt"
output_txt_file = r"C:\Users\RamyaSandhiveeran\Documents\PYTHON_SELENIUM\DataSet\IN_DataSet\IN_Output\Owen_Output.txt"


# ------------------------------
# Helper functions
# ------------------------------
def extract_after(text, keyword):
    pattern = rf"{re.escape(keyword)}\s*(.*)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str.strip(), "%B %d, %Y")
        return date_obj.strftime("%m/%d/%Y")
    except:
        return date_str


def next_day(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        return (date_obj + timedelta(days=1)).strftime("%m/%d/%Y")
    except:
        return date_str


def extract_parcel_number(text):
    match = re.search(r"Parcel Number\s*\n([^\n]+)", text)
    return match.group(1).strip() if match else ""


# ------------------------------
# Main parser for one record
# ------------------------------
def parse_raw_text(raw_text):
    parcel_number = extract_parcel_number(raw_text)
    payment_history_block = extract_after(raw_text, "Payment History:")
    tax_year_match = re.search(r"(\d{4})", payment_history_block)
    tax_year = tax_year_match.group(1) if tax_year_match else ""


    # Tax History Extraction
    tax_history_block = extract_after(raw_text, "Tax History:")
    tax_lines = [line.strip() for line in tax_history_block.splitlines() if line.strip()]


    current_year_data = ""
    for idx, line in enumerate(tax_lines):
        if re.match(r"^\d{4}$", line.strip()):
            if idx + 1 < len(tax_lines):
                current_year_data = tax_lines[idx + 1].strip()
            break


    # Extract amounts
    values = re.findall(r"\$[\d,\.]+", current_year_data)
    spring_val, fall_val, delinquency_val, total_tax_val, payments_val = values if len(values) >= 5 else ["$0.00"] * 5


    spring_float = float(spring_val.replace("$", "").replace(",", ""))
    fall_float = float(fall_val.replace("$", "").replace(",", ""))
    delinquency_float = float(delinquency_val.replace("$", "").replace(",", ""))
    total_tax_float = float(total_tax_val.replace("$", "").replace(",", ""))
    payments_float = float(payments_val.replace("$", "").replace(",", ""))


    installment_amount1 = round(total_tax_float / 2, 2)
    installment_amount2 = round(total_tax_float / 2, 2)


    paid1 = paid2 = unpaid1 = unpaid2 = 0.0


    # ------------------------------
    # PAYMENT LOGIC
    # ------------------------------
    if payments_float == total_tax_float and delinquency_float == 0.0:
        paid1 = installment_amount1
        paid2 = installment_amount2
    elif payments_float < total_tax_float and delinquency_float == 0.0:
        paid1 = installment_amount1
        unpaid2 = installment_amount2 - paid2
    elif payments_float < total_tax_float and delinquency_float > 0.0:
        paid1 = spring_float
        paid2 = fall_float
        unpaid1 = max(0, installment_amount1 - paid1)
        unpaid2 = max(0, installment_amount2 - paid2)
    elif payments_float == total_tax_float and delinquency_float > 0.0:
        paid1 = spring_float
        paid2 = fall_float
        unpaid1 = max(0, installment_amount1 - paid1)
        unpaid2 = max(0, installment_amount2 - paid2)


    fmt = lambda val: f"${val:,.2f}"
    installment_amount1_str = fmt(installment_amount1)
    installment_amount2_str = fmt(installment_amount2)
    paid1_str = fmt(paid1)
    paid2_str = fmt(paid2)
    unpaid1_str = fmt(unpaid1)
    unpaid2_str = fmt(unpaid2)


    # ------------------------------
    # Due Dates
    # ------------------------------
    due_dates_block = extract_after(raw_text, "Due Dates:")
    due_dates = re.findall(r"[A-Za-z]+\s+\d{1,2},\s+\d{4}", due_dates_block)
    due1 = format_date(due_dates[0]) if len(due_dates) > 0 else ""
    due2 = format_date(due_dates[1]) if len(due_dates) > 1 else ""
    delinquent1 = next_day(due1)
    delinquent2 = next_day(due2)


    # ------------------------------
    # Delinquencies
    # ------------------------------
    delinquencies = []
    lines = [line.strip() for line in tax_history_block.strip().splitlines() if line.strip()]
    lines = lines[2:]  # skip headers


    i = 0
    while i < len(lines):
        line = lines[i]
        match_same_line = re.match(r"(\d{4})\s+(\$[\d,\.]+)\s+(\$[\d,\.]+)\s+(\$[\d,\.]+)", line)
        if match_same_line:
            year, spring, fall, delinquent_amt = match_same_line.groups()
            delinquent_float = float(delinquent_amt.replace("$", "").replace(",", ""))
            if delinquent_float > 0:
                delinquencies.append({"payoffAmount": f"${delinquent_float:,.2f}", "taxYear": year})
            i += 1
            continue
        match_year_only = re.match(r"(\d{4})$", line)
        if match_year_only and i + 1 < len(lines):
            year = match_year_only.group(1)
            amounts_line = lines[i + 1]
            amounts = re.findall(r"\$[\d,\.]+", amounts_line)
            if len(amounts) >= 3:
                delinquent_amt = amounts[2]
                delinquent_float = float(delinquent_amt.replace("$", "").replace(",", ""))
                if delinquent_float > 0:
                    delinquencies.append({"payoffAmount": f"${delinquent_float:,.2f}", "taxYear": year})
            i += 2
            continue
        i += 1


    # ------------------------------
    # Final JSON for this record
    # ------------------------------
    return {
        "parcelNumber": parcel_number,
        "taxYear": tax_year,
        "agencies": [
            {
                "installmentAmount1": installment_amount1_str,
                "installmentDueDate1": due1,
                "installmentDelinquentDate1": delinquent1,
                "installmentPaidAmount1": paid1_str,
                "installmentUnPaidAmount1": unpaid1_str,
                "installmentAmount2": installment_amount2_str,
                "installmentDueDate2": due2,
                "installmentDelinquentDate2": delinquent2,
                "installmentPaidAmount2": paid2_str,
                "installmentUnPaidAmount2": unpaid2_str
            }
        ],
        "delinquencies": delinquencies,
        "delinquentNotes": []
    }


# ------------------------------
# Process Multiple Records
# ------------------------------
def process_multiple_records():
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()


    records = re.findall(
        r"(Property Information:.*?Due Dates:\s*May 12, 2025\s*November 10, 2025)",
        content,
        re.DOTALL
    )


    parsed_records = []
    for idx, record in enumerate(records, 1):
        print(f"Processing record #{idx} ...")
        try:
            parsed_data = parse_raw_text(record)
            parsed_records.append(parsed_data)
        except Exception as e:
            print(f"Error in record {idx}: {e}")


    # ------------------------------
    # Save output as formatted TXT file
    # ------------------------------
    with open(output_txt_file, "w", encoding="utf-8") as out:
        for idx, record in enumerate(parsed_records, 1):
            json_block = json.dumps({"parcels": [record]}, indent=4)
            out.write(f"--- Record {idx} ---\n{json_block}\n\n")
            out.write("--------------------------------------------------------------------------------\n\n")


    print(f"\nSuccessfully processed {len(parsed_records)} records.")
    print(f"Output saved to: {output_txt_file}")


# ------------------------------
# Run script
# ------------------------------
if __name__ == "__main__":
    process_multiple_records()
