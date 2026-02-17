from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import csv
import os
import time
import traceback

output_csv_path = "500global_portfolio.csv"
file_exists = os.path.isfile(output_csv_path)
with open(output_csv_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["Batch", "Pageno", "Company_Name", "Website", "LinkedIn"])

edge_options = EdgeOptions()
# edge_options.add_argument("--headless=new")
edge_options.add_argument("--disable-dev-shm-usage")
service = EdgeService(executable_path="C:/edgedriver_win64/msedgedriver.exe")

batches = [
    "Distro 1",
    "Dojo I",
    "Dojo II",
    "Dojo III",
    "Egypt Scale Up1",
    "Eurasia 7",
    "Eurasia 8",
    "Eurasia 9",
    "GA 10",
    "GA 11",
    "GA 12",
    "GA 13",
    "GA 14",
    "GA 15",
    "GA 16",
    "GA 17",
    "GA 18",
    "GA 19",
    "GA 1",
    "GA 20",
    "GA 21",
    "GA 22",
    "GA 23",
    "GA 24",
    "GA 25",
    "GA 26",
    "GA 27",
    "GA 28",
    "GA 29",
    "GA 2",
    "GA 30",
    "GA 32",
    "GA 33",
    "GA 34",
    "GA 35",
    "GA 3",
    "GA 4",
    "GA 5",
    "GA 6",
    "GA 7",
    "GA 8",
    "GA 9",
    "Georgia 3",
    "Georgia 4",
    "Georgia 5",
    "Georgia 6",
    "Georgia 7",
    "Lucha - NONE",
    "Lucha 10",
    "Lucha 11",
    "Lucha 12",
    "Lucha 14",
    "Lucha 15",
    "Lucha 18",
    "Lucha 1",
    "Lucha 2",
    "Lucha 3",
    "Lucha 4",
    "Lucha 5",
    "Lucha 6",
    "Lucha 7",
    "Lucha 8",
    "Lucha 9",
    "MENA 10",
    "Mena 1",
    "Mena 2",
    "Mena 4",
    "MENA 5",
    "MENA 6",
    "MENA 7",
    "MENA 8",
    "MENA 9",
    "Misk 1",
    "Misk 2",
    "Misk 3",
    "Saola",
    "SF 36",
]


def is_positive_integer(s):
    return s.isdigit()


def launch_page(driver, batch, pageno, maxpageno):
    wait = WebDriverWait(driver, 20)
    company_cards = []  # Initialize to handle exceptions gracefully

    try:
        url = f"https://500.co/portfolio?batch={batch}&page={pageno}"
        driver.get(url)
        print(f"Navigating to {url}...")
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//h2[text()='Portfolio Companies']")
            )
        )
        print("Page loaded. Waiting for company cards to appear...")

        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        company_card_selector = "//div[contains(@class, 'flex p-4 flex-col-reverse') and contains(@class, 'bg-white') and contains(@class, 'rounded-[7px]') and contains(@class, 'border')]"
        try:
            wait.until(
                EC.presence_of_all_elements_located((By.XPATH, company_card_selector))
            )
            company_cards = driver.find_elements(By.XPATH, company_card_selector)
        except TimeoutException:
            print("No company cards found on this page.")

        print("No of card_elements:", len(company_cards))

        if not company_cards:
            print(
                "No company cards found after dynamic load. Check selectors and page structure."
            )

        if pageno == 1:
            print("Waiting for page footer to appear...")
            page_footer_selector = "nav > ul > li > a"
            try:
                wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, page_footer_selector)
                    )
                )
                page_no_elems = driver.find_elements(
                    By.CSS_SELECTOR, page_footer_selector
                )
                page_nos = []
                for page_no_elem in page_no_elems:
                    page_nos.append(page_no_elem.text)
                    if is_positive_integer(page_no_elem.text):
                        maxpageno = max(maxpageno, int(page_no_elem.text))
                print("page_nos", page_nos)
                print("maxpageno", maxpageno)
            except TimeoutException:
                print("Page footer not found, assuming a single page.")

        print(f"Found {len(company_cards)} company cards on {url}.")
    except Exception as e:
        print(e)
        traceback.print_exc()

    return company_cards, maxpageno


def scrape_500global_portfolio(batch):
    try:
        driver = webdriver.Edge(service=service, options=edge_options)
    except Exception as e:
        print(f"Error setting up Selenium WebDriver: {e}")
        print(
            "Attempting to initialize WebDriver without explicitly providing service (might work if msedgedriver is in PATH)."
        )
        driver = webdriver.Edge(options=edge_options)

    pageno = 1
    maxpageno = 1
    scraped_data = []

    while pageno <= maxpageno:
        company_cards, maxpageno = launch_page(driver, batch, pageno, maxpageno)

        for i, card_element in enumerate(company_cards):
            company_name = "N/A"
            website_link = "N/A"
            linkedin_link = "N/A"

            try:
                card_soup = BeautifulSoup(
                    card_element.get_attribute("outerHTML"), "html.parser"
                )

                # Try to find company name:
                # 1. Look for a span with 'column-name' class
                name_span = card_soup.find("span", class_="column-name")
                if name_span and name_span.get_text(strip=True):
                    company_name = name_span.get_text(strip=True)
                else:
                    # 2. Look for an <a> tag that might act as the name and main website link
                    # Filter out social links by checking href
                    # This targets the main company link with text.
                    # Adjusted class check to account for potential variations like 'text-xl' or 'text-2xl'
                    name_link = card_soup.find(
                        "a",
                        class_=lambda c: (
                            c
                            and ("text-xl" in c or "text-2xl" in c)
                            and "font-tobias" in c
                        ),
                        href=True,
                    )
                    if (
                        name_link
                        and "linkedin.com" not in name_link["href"]
                        and "twitter.com" not in name_link["href"]
                    ):
                        company_name = name_link.get_text(strip=True)
                        website_link = name_link["href"]

                if website_link == "N/A":
                    # Look for any <a> tag within the card that has an http/https href
                    # and is not LinkedIn, Twitter, or an internal /companies/ link.
                    all_links = card_soup.find_all("a", href=True)
                    for link in all_links:
                        href = link["href"]
                        if (
                            href.startswith("http")
                            and "linkedin.com" not in href
                            and "twitter.com" not in href
                            and "500.co/companies" not in href
                        ):  # Exclude internal "learn more" links
                            website_link = href
                            break  # Assume the first valid external link is the main website

                linkedin_link_element = card_soup.find(
                    "a", href=lambda href: href and "linkedin.com" in href
                )
                if linkedin_link_element:
                    linkedin_link = linkedin_link_element["href"]

            except Exception as e:
                print(f"Error processing card {i}: {e}")
                traceback.print_exc()

            scraped_data.append(
                [
                    batch.replace("%20", "_"),
                    pageno,
                    company_name,
                    website_link,
                    linkedin_link,
                ]
            )
        pageno += 1
        time.sleep(5)

    driver.quit()
    print(
        f"Returning {len(scraped_data)} rows from scrape_500global_portfolio: {batch}."
    )
    return scraped_data


def is_string_in_csv(search_string):
    with open(output_csv_path, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if any(search_string in field for field in row):
                return True
    return False

if __name__ == "__main__":
    all_data = []
    for batch in batches:
        if is_string_in_csv(batch.replace(" ", "_")):
            continue
        all_data.extend(scrape_500global_portfolio(batch.replace(" ", "%20")))
        try:
            with open(
                output_csv_path, "a", newline="", encoding="utf-8"
            ) as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerows(all_data)
            print(f"Scraping complete. {len(all_data)} Data rows added to {output_csv_path}")
        except IOError as e:
            print(f"Error writing to CSV file: {e}")
            traceback.print_exc()
