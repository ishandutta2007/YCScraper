from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import csv
import os
import pprint as pp
import time

edge_options = Options()
# edge_options.add_argument("--headless=new")
service = Service(executable_path="C:/edgedriver_win64/msedgedriver.exe")

driver = webdriver.Edge(service=service, options=edge_options)
wait = WebDriverWait(driver, 10)

cwd = os.getcwd()
print("Current Working Directory:", cwd)
csv_file_path = os.path.join(cwd, "yc_founders_social.csv")
print("csv_file_path:", csv_file_path)


def is_string_in_csv(search_string):
    with open(csv_file_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if any(search_string in field for field in row):
                return True
    return False


def check_swapped_presense(batch):
    batch_swapped = "_".join(batch.replace("%20", "_").split("_")[::-1])
    return is_string_in_csv(batch_swapped)


# Generate possible YC batch codes (S05 to S26, W06 to W26)
batches = []
for year in range(2026, 2004, -1):
    batch = f"Summer%20{year:04d}"
    if not check_swapped_presense(batch):
        batches.append(batch)
    if year >= 2006:
        batch = f"Winter%20{year:04d}"
        if not check_swapped_presense(batch):
            batches.append(batch)

base_url = "https://www.ycombinator.com"
file_exists = os.path.isfile(csv_file_path)
with open(csv_file_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(
            ["Batch", "Company", "Founder_or_company", "LinkedIn", "Twitter", "Github"]
        )

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
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        company_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='/companies/']")
        company_urls = set()  # Use set to avoid duplicates
        for link in company_links:
            href = link.get_attribute("href")
            if href and "/companies/" in href and "batch" not in href:
                full_url = base_url + href if href.startswith("/") else href
                company_urls.add(full_url)

        print(f"Found {len(company_urls)} companies in batch {batch}:")
        pp.pprint(company_urls)
        data = []
        for company_url in company_urls:
            try:
                driver.get(company_url)
                time.sleep(3)

                company_name = company_url.split("/")[-1].replace("-", "_").title()
                founder_elements = driver.find_elements(
                    By.CSS_SELECTOR, "div.ycdc-card-new, div.ycdc-card"
                )
                print(
                    f"company_name={company_name} has {len(founder_elements)} founders"
                )
                for founder_el in founder_elements:
                    try:
                        founder_name_el = founder_el.find_element(
                            By.CSS_SELECTOR, "div.text-xl"
                        )
                        # print("founder_name_el", founder_name_el)
                        founder_name = founder_name_el.text if founder_name_el else None
                        print("founder_name", founder_name)

                        linkedin_el = (
                            founder_el.find_element(
                                By.CSS_SELECTOR, "a[href*='linkedin']"
                            )
                            if founder_el.find_elements(
                                By.CSS_SELECTOR, "a[href*='linkedin']"
                            )
                            else None
                        )
                        linkedin = (
                            linkedin_el.get_attribute("href") if linkedin_el else None
                        )

                        twitter_el = (
                            founder_el.find_element(
                                By.CSS_SELECTOR, "a[href*='twitter'], a[href*='x.com']"
                            )
                            if founder_el.find_elements(
                                By.CSS_SELECTOR, "a[href*='twitter'], a[href*='x.com']"
                            )
                            else None
                        )
                        twitter = (
                            twitter_el.get_attribute("href") if twitter_el else None
                        )

                        github_el = (
                            founder_el.find_element(
                                By.CSS_SELECTOR, "a[href*='github'], a[href*='x.com']"
                            )
                            if founder_el.find_elements(
                                By.CSS_SELECTOR, "a[href*='github']"
                            )
                            else None
                        )
                        github = github_el.get_attribute("href") if github_el else None

                        if linkedin or twitter:  # Only add if at least one social link
                            batch_swapped = "_".join(
                                batch.replace("%20", "_").split("_")[::-1]
                            )
                            data.append(
                                [
                                    batch_swapped,
                                    company_name,
                                    founder_name,
                                    linkedin or "",
                                    twitter or "",
                                    github or "",
                                ]
                            )
                            print(
                                f"Added: {batch_swapped}, {company_name}, {founder_name}, {linkedin or ''}, {twitter or ''}, {github or ''}"
                            )
                    except Exception as e:
                        print(f"Error extracting founder from {company_url}: {e}")
                        continue

            except Exception as e:
                print(f"Error processing company {company_url}: {e}")
                continue
        with open(csv_file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)
        print(
            f"Scraping complete. Data saved to yc_founders_social.csv with {len(data)} entries."
        )
finally:
    driver.quit()

