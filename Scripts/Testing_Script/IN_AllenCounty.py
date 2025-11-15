import os
import re
import time
from dotenv import load_dotenv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

load_dotenv()

# ------------------------------
# Setup Chrome
# ------------------------------
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


driver = webdriver.Chrome(service=service, options=chrome_options)


# ------------------------------
# Helper function
# ------------------------------
def normalize_string(s):
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()


# ------------------------------
# Variables
# ------------------------------
county_site_url = "https://lowtaxinfo.com/allencounty"
partial_name = "Smith Karen K"
partial_address = "6201 Thimlar Rd New Haven, IN 46774"

normalized_partial_name_query = normalize_string(partial_name)
normalized_partial_address = normalize_string(partial_address)


# ------------------------------
# STEP 1: Open the website
# ------------------------------
try:
    driver.get(county_site_url)
    driver.maximize_window()
    ("URL loaded successfully")
except Exception as e:
    print("Step 1 failed:", e)


# ------------------------------
# STEP 2: Enter Owner Name and Address, then Wait for Table to Load
# ------------------------------
try:
    # Extract first 2 or 3 words from the owner name
    owner_words = partial_name.split()
    if len(owner_words) <= 2:
        owner_input_text = " ".join(owner_words)
    else:
        owner_input_text = " ".join(owner_words[:2])

    # Wait for the owner name input box and type the name
    owner_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "owner-name"))
    )
    owner_input.clear()
    owner_input.send_keys(owner_input_text)
    (f"Owner name entered: {owner_input_text}")

    # Wait for the address input box and type the address
    address_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "address"))
    )
    address_input.clear()
    address_input.send_keys(partial_address)
    address_input.send_keys(Keys.ENTER)
    (f"Address entered: {partial_address}")

    # Wait for the table to appear
    table_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".table.table-sm.table-hover"))
    )

    # Wait until rows are loaded
    WebDriverWait(driver, 30).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr")) > 0
    )

    ("Table is loaded successfully.\n")


except TimeoutException:
    print("Table did not load in time.")
except Exception as e:
    print("Step 2 failed:", e)


# ------------------------------
# STEP 3 & 4: Detect Pagination and Extract All Table Rows
# ------------------------------
try:
    # Default to single page
    start_page = 1
    end_page = 1

    # Try detecting pagination
    try:
        pagination = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.pagination"))
        )

        # Extract all page number elements
        page_links = pagination.find_elements(By.CSS_SELECTOR, "li.page-item a.page-link")

        page_numbers = []
        for link in page_links:
            text = link.text.strip()
            if text.isdigit():
                page_numbers.append(int(text))

        if page_numbers:
            start_page = min(page_numbers)
            end_page = max(page_numbers)
            ("Pagination detected: Start Page = {start_page}, End Page = {end_page}")
        else:
            print("Pagination not found, assuming single page result.")


    except TimeoutException:
        ("No pagination visible — only one page of results.")
        start_page = 1
        end_page = 1

    # Loop through each page and extract table rows
    for page in range(start_page, end_page + 1):
        (f"Processing Page {page}...")

        # Build URL manually if multiple pages exist
        if end_page > 1:
            page_url = f"https://lowtaxinfo.com/allencounty?address={partial_address.replace(' ', '%20')}&page={page}"
            driver.get(page_url)

        # Wait for table rows to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr"))
        )

        # Extract all rows
        rows = driver.find_elements(By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr")

        if not rows:
            print(f"No rows found on Page {page}")
            continue

        # Print row data
        for i, row in enumerate(rows, start=1):
            (f"{page}.{i}. {row.text.strip()}")

        (f"Completed extracting Page {page} ({len(rows)} rows)")

except TimeoutException:
    print("Table did not load properly on one of the pages.")
except Exception as e:
    print("Step 3 & 4 failed:", e)


# ------------------------------
# STEP 5: Find Matching Record
# ------------------------------
try:
    # Reuse the normalize_string function from before
    matched_found = False

    # Loop through each page again
    for page in range(start_page, end_page + 1):
        (f"\nSearching for match in Page {page}...")

        # Build URL manually if multiple pages exist
        if end_page > 1:
            page_url = f"https://lowtaxinfo.com/allencounty?address={partial_address.replace(' ', '%20')}&page={page}"
            driver.get(page_url)

        # Wait for table rows to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr"))
        )

        rows = driver.find_elements(By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr")

        for i, row in enumerate(rows, start=1):
            row_text = row.text.strip()
            normalized_row = normalize_string(row_text)

            if normalized_partial_name_query in normalized_row and normalized_partial_address in normalized_row:
                (f"\nMatched Record Found on Page {page}, Row {i}:")
                (row_text)
                matched_found = True
                matched_row_text = row_text
                break  # stop after first match

        if matched_found:
            break  # stop searching if match found

    if not matched_found:
        print("No matching record found in any page.")


except Exception as e:
    print("Step 5 failed:", e)


# ------------------------------
# STEP 6: Extract Duplicate# and Generate URL
# ------------------------------
try:
    # Ensure matched_row_text is defined from Step 5
    duplicate_match = re.search(r"Duplicate#\s*(\d+)", matched_row_text)


    if duplicate_match:
        duplicate_value = duplicate_match.group(1)
        (f"Duplicate# extracted: {duplicate_value}")

        # Get current year
        current_year = datetime.now().year

        # Generate URL in the requested format
        generated_url = f"https://lowtaxinfo.com/allencounty/{duplicate_value}-{current_year}"
        (f"Generated URL: {generated_url}")

    else:
        print("Duplicate# not found in the matched record.")


except Exception as e:
    print("Step 6 failed:", e)


# ------------------------------
# STEP 7: Navigate to Generated URL and Wait for Page Load
# ------------------------------
try:
    # Navigate to the URL generated in Step 6
    driver.get(generated_url)
    
    # Wait for the element with ID 'parcel' to appear
    parcel_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "parcel"))
    )

    time.sleep(4)
    ("Navigated to the generated URL and loaded successfully.")

except TimeoutException:
    print("'parcel' element did not load in time.")
except Exception as e:
    print("Step 7 failed:", e)


# ------------------------------
# STEP 8: Extract Property Information
# ------------------------------
try:
    # Wait for the element with ID 'info' to appear
    info_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "info"))
    )
    time.sleep(2)

    # Get the raw text of the 'info' element
    property_info_text = info_element.text.strip()

    print("\nProperty Information:")
    print(property_info_text)

except TimeoutException:
    print("'info' element did not load in time.")
except Exception as e:
    print("Step 8 failed:", e)


# ------------------------------
# STEP 9: Extract Tax Information
# ------------------------------
try:
    # Wait for the element with ID 'billing-detail' to appear
    billing_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "billing-detail"))
    )
    time.sleep(2)

    # Get the raw text of the 'billing-detail' element
    tax_info_text = billing_element.text.strip()

    print("\nTax Information:")
    print(tax_info_text)


except TimeoutException:
    print("'billing-detail' element did not load in time.")
except Exception as e:
    print("Step 9 failed:", e)


# ------------------------------
# STEP 10: Extract Payment History
# ------------------------------
try:
    # Wait for the element with ID 'payment-history' to appear
    payment_history_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "payment-history"))
    )
    time.sleep(2)

    # Get the raw text of the 'payment-history' element
    payment_history_text = payment_history_element.text.strip()

    print("\nPayment History:")
    print(payment_history_text)

except TimeoutException:
    print("'payment-history' element did not load in time.")
except Exception as e:
    print("Step 10 failed:", e)


# ------------------------------
# STEP 11: Extract Tax History
# ------------------------------
try:
    # Wait for the element with ID 'tax-history' to appear
    tax_history_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "tax-history"))
    )
    time.sleep(2)

    # Get the raw text of the 'tax-history' element
    tax_history_text = tax_history_element.text.strip()

    print("\nTax History:")
    print(tax_history_text)

except TimeoutException:
    print("'tax-history' element did not load in time.")
except Exception as e:
    print("Step 11 failed:", e)


# ------------------------------
# STEP 12: Extract Property Tax Due Dates
# ------------------------------
try:
    indy_url = "https://www.indy.gov/activity/find-property-tax-due-dates"
    driver.get(indy_url)

    # Wait for the second <ul> to load (using XPath)
    ul_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "(//ul)[2]"))
    )
    time.sleep(2)

    # Extract the raw text from the <ul>
    tax_due_dates_text = ul_element.text.strip()

    print("\nDue Dates:")
    print(tax_due_dates_text)


except TimeoutException:
    print("Tax Due Dates <ul> did not load in time.")
except Exception as e:
    print("Step 12 failed:", e)


finally:
    driver.quit()
    ("\nBrowser closed successfully.")