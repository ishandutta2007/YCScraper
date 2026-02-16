import csv
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service  # Changed to Edge
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager  # Changed to Edge manager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pprint as pp
import os

# Setup Edge driver with automatic management
service = Service(executable_path="C:/edgedriver_win64/msedgedriver.exe")
driver = webdriver.Edge(service=service)
wait = WebDriverWait(driver, 10)

# Generate possible YC batch codes (S05 to S26, W06 to W26)
batches = []
for year in range(2026, 2025, -1):
    batches.append(f"Summer%20{year:04d}")
    if year >= 6:
        batches.append(f"Winter%20{year:04d}")

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
        print(f"which are: ")
        pp.pprint(company_urls)

        for company_url in company_urls:
            try:
                driver.get(company_url)
                time.sleep(2)

                company_name = company_url.split("/")[-1].replace("-"."_").title()
                founder_elements = driver.find_elements(By.CSS_SELECTOR, "div.ycdc-card-new")
                print(f"company_name={company_name} has {len(founder_elements)} founders")
                for founder_el in founder_elements:
                    try:
                        founder_name_el = founder_el.find_element(By.CSS_SELECTOR, "div.text-xl")
                        founder_name = founder_name_el.text if founder_name_el else None

                        linkedin_el = founder_el.find_element(By.CSS_SELECTOR, "a[href*='linkedin']") if founder_el.find_elements(By.CSS_SELECTOR, "a[href*='linkedin']") else None
                        linkedin = linkedin_el.get_attribute('href') if linkedin_el else None

                        twitter_el = founder_el.find_element(By.CSS_SELECTOR, "a[href*='twitter'], a[href*='x.com']") if founder_el.find_elements(By.CSS_SELECTOR, "a[href*='twitter'], a[href*='x.com']") else None
                        twitter = twitter_el.get_attribute('href') if twitter_el else None

                        github_el = founder_el.find_element(By.CSS_SELECTOR, "a[href*='github'], a[href*='x.com']") if founder_el.find_elements(By.CSS_SELECTOR, "a[href*='github']") else None
                        github = github_el.get_attribute('href') if github_el else None

                        if linkedin or twitter:  # Only add if at least one social link
                            data.append([company_name, batch.replace('%20','_'), founder_name, linkedin or '', twitter or '', github or ''])
                            print(f"Added: {company_name} - {founder_name}")

                    except Exception as e:
                        print(f"Error extracting founder from {company_url}: {e}")
                        continue

            except Exception as e:
                print(f"Error processing company {company_url}: {e}")
                continue

finally:
    driver.quit()

file_path = 'yc_founders_social.csv'
file_exists = os.path.isfile(file_path)
with open(file_path, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(['Company', 'Batch', 'Founder_or_company', 'LinkedIn', 'Twitter', 'Github'])
    writer.writerows(data)

print(f"Scraping complete. Data saved to yc_founders_social.csv with {len(data)} entries.")
