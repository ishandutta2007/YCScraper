import csv
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service  # Changed to Edge
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager  # Changed to Edge manager
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Setup Edge driver with automatic management
service = Service(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(service=service)  # Changed to Edge
wait = WebDriverWait(driver, 10)

# Generate possible YC batch codes (S05 to S26, W06 to W26)
batches = []
for year in range(5, 27):
    batches.append(f"S{year:02d}")
    if year >= 6:
        batches.append(f"W{year:02d}")

data = []
base_url = "https://www.ycombinator.com"

try:
    for batch in batches:
        print(f"Processing batch: {batch}")
        url = f"{base_url}/companies?batch={batch}"
        driver.get(url)
        time.sleep(3)

        # Scroll to load all companies in the batch
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Find all company links (adjust selector if needed by inspecting the page)
        company_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='/companies/']")
        company_urls = set()  # Use set to avoid duplicates
        for link in company_links:
            href = link.get_attribute('href')
            if href and '/companies/' in href and 'batch' not in href:
                full_url = base_url + href if href.startswith('/') else href
                company_urls.add(full_url)

        print(f"Found {len(company_urls)} companies in batch {batch}")

        for company_url in company_urls:
            try:
                driver.get(company_url)
                time.sleep(2)

                # Get company name (adjust selector if needed)
                company_name = driver.find_element(By.TAG_NAME, "h1").text

                # Find founders section (adjust XPath/CSS if needed)
                # Assuming founders are in divs with class containing 'founder' or similar
                founder_elements = driver.find_elements(By.CSS_SELECTOR, ".founder, [data-testid='founder'], div[contains(@class, 'founder')]")
                if not founder_elements:
                    # Alternative: look for section with 'Founders' text
                    founders_section = driver.find_element(By.XPATH, "//*[contains(text(), 'Founders') or contains(text(), 'Team')]//following-sibling::*")
                    founder_elements = founders_section.find_elements(By.TAG_NAME, "div")  # Adjust as needed

                for founder_el in founder_elements:
                    try:
                        # Get founder name (adjust selector)
                        name_elements = founder_el.find_elements(By.TAG_NAME, "h3") or founder_el.find_elements(By.TAG_NAME, "h4") or founder_el.find_elements(By.CSS_SELECTOR, ".name")
                        founder_name = next((el.text for el in name_elements if el.text.strip()), None)
                        if not founder_name:
                            continue

                        # Get LinkedIn link
                        linkedin_el = founder_el.find_element(By.CSS_SELECTOR, "a[href*='linkedin']") if founder_el.find_elements(By.CSS_SELECTOR, "a[href*='linkedin']") else None
                        linkedin = linkedin_el.get_attribute('href') if linkedin_el else None

                        # Get Twitter/X link
                        twitter_el = founder_el.find_element(By.CSS_SELECTOR, "a[href*='twitter'], a[href*='x.com']") if founder_el.find_elements(By.CSS_SELECTOR, "a[href*='twitter'], a[href*='x.com']") else None
                        twitter = twitter_el.get_attribute('href') if twitter_el else None

                        if linkedin or twitter:  # Only add if at least one social link
                            data.append([company_name, founder_name, linkedin or '', twitter or ''])
                            print(f"Added: {company_name} - {founder_name}")

                    except Exception as e:
                        print(f"Error extracting founder from {company_url}: {e}")
                        continue

            except Exception as e:
                print(f"Error processing company {company_url}: {e}")
                continue

finally:
    driver.quit()

# Save to CSV
with open('yc_founders_social.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Company', 'Founder', 'LinkedIn', 'Twitter'])
    writer.writerows(data)

print(f"Scraping complete. Data saved to yc_founders_social.csv with {len(data)} entries.")