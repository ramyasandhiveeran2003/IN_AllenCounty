import os
import re
import time
import urllib.parse
import requests
import fitz  # PyMuPDF
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from driver_.chromeBrowser import driver_access
from datetime import datetime

load_dotenv()


# ------------------------------
# Helper function
# ------------------------------
def normalize_string(s):
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

# Example inputs
# search_type = "address"
# search_value = "6201 Thimlar Rd New Haven, IN 46774"
# name = "Smith Karen K"


def scrape_data(search_type, search_value, name):
    data = ""
    driver = driver_access()
    wait = WebDriverWait(driver, 15)
    normalized_partial_name = normalize_string(name)
    normalized_partial_address = normalize_string(search_value)


    try:
        if search_type.lower() != "address":
            ("Only 'address' search_type is supported for this County.")
            return None


        driver = driver_access()
        county_site_url = "https://lowtaxinfo.com/allencounty"


        # ------------------------------
        # STEP 1: Open the website
        # ------------------------------
        try:
            driver.get(county_site_url)
            driver.maximize_window()
            ("URL loaded successfully.\n")
        except Exception as e:
            data += f"Step 1 failed: {e}\n"


        # ------------------------------
        # STEP 2: Enter Owner Name and Address, then Wait for Table to Load
        # ------------------------------
        try:
            # Extract first 2 or 3 words from the owner name
            owner_words = name.split()
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
            address_input.send_keys(search_value)
            address_input.send_keys(Keys.ENTER)
            (f"Address entered: {search_value}")

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
            data +=("Table did not load in time.")
        except Exception as e:
            data += f"Step 2 failed: {e}\n"


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
                    if text.isdigit():  # ignore 'Previous', 'Next', '...'
                        page_numbers.append(int(text))

                if page_numbers:
                    start_page = min(page_numbers)
                    end_page = max(page_numbers)
                    (f"Pagination detected: Start Page = {start_page}, End Page = {end_page}")
                else:
                    data +=("Pagination not found, assuming single page result.")

            except TimeoutException:
                ("No pagination visible — only one page of results.")
                start_page = 1
                end_page = 1

            # Loop through each page and extract table rows
            for page in range(start_page, end_page + 1):
                (f"\nProcessing Page {page}...")

                # Build URL manually if multiple pages exist
                if end_page > 1:
                    page_url = f"https://lowtaxinfo.com/allencounty?address={search_value.replace(' ', '%20')}&page={page}"
                    driver.get(page_url)

                # Wait for table rows to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr"))
                )

                # Extract all rows
                rows = driver.find_elements(By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr")

                if not rows:
                    data +=(f"No rows found on Page {page}")
                    continue

                # Print row data
                for i, row in enumerate(rows, start=1):
                    (f"{page}.{i}. {row.text.strip()}")

                (f"Completed extracting Page {page} ({len(rows)} rows)")


        except TimeoutException:
            data +=("Table did not load properly on one of the pages.")
        except Exception as e:
            data += f"Step 3 & 4 failed: {e}\n"

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
                    page_url = f"https://lowtaxinfo.com/allencounty?address={search_value.replace(' ', '%20')}&page={page}"
                    driver.get(page_url)

                # Wait for table rows to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr"))
                )

                rows = driver.find_elements(By.CSS_SELECTOR, ".table.table-sm.table-hover tbody tr")

                for i, row in enumerate(rows, start=1):
                    row_text = row.text.strip()
                    normalized_row = normalize_string(row_text)

                    if normalized_partial_name in normalized_row and normalized_partial_address in normalized_row:
                        (f"\nMatched Record Found on Page {page}, Row {i}:")
                        (row_text)
                        matched_found = True
                        matched_row_text = row_text
                        break  # stop after first match

                if matched_found:
                    break  # stop searching if match found

            if not matched_found:
                data +=("No matching record found in any page.")

        except Exception as e:
            data += f"Step 5 failed: {e}\n"

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
                data +=("Duplicate# not found in the matched record.")

        except Exception as e:
            data += f"Step 6 failed: {e}\n"


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
            data +=("'parcel' element did not load in time.")
        except Exception as e:
            data += f"Step 7 failed: {e}\n"

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

            data +=("\nProperty Information:\n")
            data +=(property_info_text)+"\n"

        except TimeoutException:
            data +=("'info' element did not load in time.")
        except Exception as e:
            data += f"Step 8 failed: {e}\n"


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

            data +=("\nTax Information:\n")
            data +=(tax_info_text)+"\n"

        except TimeoutException:
            data +=("'billing-detail' element did not load in time.")
        except Exception as e:
            data += f"Step 9 failed: {e}\n"


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

            data +=("\nPayment History:\n")
            data +=(payment_history_text)+"\n"

        except TimeoutException:
            data +=("'payment-history' element did not load in time.")
        except Exception as e:
            data += f"Step 10 failed: {e}\n"


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

            data +=("\nTax History:\n")
            data +=(tax_history_text)+"\n"

        except TimeoutException:
            data +=("'tax-history' element did not load in time.")
        except Exception as e:
            data += f"Step 11 failed: {e}\n"


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

            data +=("\nDue Dates:\n")
            data +=(tax_due_dates_text)+"\n"

        except TimeoutException:
            data+=("Tax Due Dates <ul> did not load in time.")
        except Exception as e:
            data += f"Step 12 failed: {e}\n"
    except Exception as e:
        data +=(f"Unexpected error: {e}")
        return None


    finally:
        driver.quit()
        ("\nBrowser closed successfully.")


        return data


# Call the function
result = scrape_data(search_type, search_value, name)


# Print output
print(result)
