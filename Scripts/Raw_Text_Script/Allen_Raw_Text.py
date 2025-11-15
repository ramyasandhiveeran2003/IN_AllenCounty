import os
import re
import time
from dotenv import load_dotenv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

load_dotenv()

# ============================================
# Setup Chrome
# ============================================
chrome_binary = os.getenv('localPath') + '/chrome-win64/chrome.exe'
service = ChromeService(executable_path=os.getenv('localPath') + '/chromedriver.exe')
chrome_options = Options()
chrome_options.binary_location = chrome_binary
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--allow-insecure-localhost")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--ignore-ssl-errors")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])


# ============================================
# Helper functions
# ============================================
def normalize_string(s):
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()


def log_to_file(content):
    """Append text to the output file"""
    with open("perrycounty.rawtext.txt", "a", encoding="utf-8") as f:
        f.write(content + "\n")


# ============================================
# Input Arrays
# ============================================
addresses = [
    "10 Tulip Tree Ln Tell City, IN 47586",
    "10 Wm Tell Blvd Tell City, IN 47586",
    "10 Clifton Heights Cannelton, IN 47520",
    "10 Pleasant Valley Dr Cannelton, IN 47520",
    "1810 10th Street Tell City, IN 47586",
    "10 Commerce Dr Troy, IN 47588",
    "10 11th St Tell City, IN 47586",
    "10 Rolling Pines Drive Tell City, IN 47586",
    "727 Washington St Lot 10 Troy, IN 47588",
    "910 Main St Tell City, IN 47586"
]


names = [
    "Parke, Eric M & Emily L",
    "Magayao, Sweden B & Maria Ligaya P",
    "Nugent, Tiffany Suzanne",
    "Perrine, Nancee A",
    "Pekinpaugh, Mary A",
    "Linne, Jason",
    "Roberts, Elizabeth A, Christine L Beeler, Theresa J Lipps, Kevin E Paulin",
    "Miller, Earl P & Carlene M",
    "Cronin, Randy",
    "Cedar Crest Llc"
]


# ============================================
# Process Each Record
# ============================================

for idx, (partial_address, partial_name) in enumerate(zip(addresses, names), start=1):
    try:
        # Header for each record
        header = f"""
--------------------------------------------------------------------------------
{idx}. Search Address: {partial_address}
--------------------------------------------------------------------------------
"""
        print(header)
        log_to_file(header)

        driver = webdriver.Chrome(service=service, options=chrome_options)

        normalized_partial_name_query = normalize_string(partial_name)
        normalized_partial_address = normalize_string(partial_address)


        county_site_url = "https://lowtaxinfo.com/perrycounty"

        # ------------------------------
        # STEP 1: Open the website
        # ------------------------------
        driver.get(county_site_url)
        driver.maximize_window()
        ("Step 1: URL loaded successfully.\n")


        # ------------------------------
        # STEP 2: Enter Owner Name and Address
        # ------------------------------
        owner_words = partial_name.split()
        owner_input_text = " ".join(owner_words[:2]) if len(owner_words) > 2 else partial_name

        owner_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "owner-name"))
        )
        owner_input.clear()
        owner_input.send_keys(owner_input_text)
        (f"Owner name entered: {owner_input_text}")

        address_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "address"))
        )
        address_input.clear()
        address_input.send_keys(partial_address)
        address_input.send_keys(Keys.ENTER)
        (f"Address entered: {partial_address}")

        # Wait for table to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".table.table-sm.table-hover"))
        )
        WebDriverWait(driver, 30).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr")) > 0
        )
        ("Table is loaded successfully.\n")


        # ------------------------------
        # STEP 3–4: Pagination & Extract Rows
        # ------------------------------
        start_page = 1
        end_page = 1
        try:
            pagination = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.pagination"))
            )
            page_links = pagination.find_elements(By.CSS_SELECTOR, "li.page-item a.page-link")
            page_numbers = [int(l.text.strip()) for l in page_links if l.text.strip().isdigit()]
            if page_numbers:
                start_page, end_page = min(page_numbers), max(page_numbers)
        except TimeoutException:
            pass


        matched_row_text = None
        matched_found = False


        # ------------------------------
        # STEP 5: Find Matching Record
        # ------------------------------
        for page in range(start_page, end_page + 1):
            if end_page > 1:
                driver.get(f"{county_site_url}?address={partial_address.replace(' ', '%20')}&page={page}")


            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr"))
            )
            rows = driver.find_elements(By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr")


            for row in rows:
                row_text = row.text.strip()
                print(row_text)
                normalized_row = normalize_string(row_text)
                if normalized_partial_name_query in normalized_row and normalized_partial_address in normalized_row:
                    (f"Matched Record Found: {row_text}")
                    matched_found = True
                    matched_row_text = row_text
                    break
            if matched_found:
                break


        if not matched_found:
            log_to_file("No matching record found.")
            driver.quit()
            continue

        # ------------------------------
        # STEP 6: Extract Duplicate# and Generate URL
        # ------------------------------
        duplicate_match = re.search(r"Duplicate#\s*(\d+)", matched_row_text)
        if duplicate_match:
            duplicate_value = duplicate_match.group(1)
            current_year = datetime.now().year
            generated_url = f"https://lowtaxinfo.com/perrycounty/{duplicate_value}-{current_year}"
            (f"Generated URL: {generated_url}")
        else:
            log_to_file("Duplicate# not found.")
            driver.quit()
            continue


        # ------------------------------
        # STEP 7: Navigate to URL
        # ------------------------------
        driver.get(generated_url)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "parcel")))
        time.sleep(3)
        ("Navigated and loaded successfully.")


        # ------------------------------
        # STEP 8: Property Info
        # ------------------------------
        info_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "info"))
        )
        property_info_text = info_element.text.strip()
        log_to_file("\nProperty Information:\n" + property_info_text)


        # ------------------------------
        # STEP 9: Tax Info
        # ------------------------------
        billing_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "billing-detail"))
        )
        tax_info_text = billing_element.text.strip()
        log_to_file("\nTax Information:\n" + tax_info_text)


        # ------------------------------
        # STEP 10: Payment History
        # ------------------------------
        payment_history_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "payment-history"))
        )
        payment_history_text = payment_history_element.text.strip()
        log_to_file("\nPayment History:\n" + payment_history_text)


        # ------------------------------
        # STEP 11: Tax History
        # ------------------------------
        tax_history_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "tax-history"))
        )
        tax_history_text = tax_history_element.text.strip()
        log_to_file("\nTax History:\n" + tax_history_text)


        # ------------------------------
        # STEP 12: Due Dates (Indy)
        # ------------------------------
        indy_url = "https://www.indy.gov/activity/find-property-tax-due-dates"
        driver.get(indy_url)
        ul_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "(//ul)[2]"))
        )
        tax_due_dates_text = ul_element.text.strip()
        log_to_file("\nDue Dates:\n" + tax_due_dates_text)


    except Exception as e:
        log_to_file(f"Error in record {idx}: {e}")
    finally:
        driver.quit()
        log_to_file("\n==========================================================================================\n")


print(" All records processed. Output saved in allen.rawtext.txt")
