from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# from selenium.webdriver.chrome.options import Options as ChromeOptions # Assuming Chrome, but can be Edge
from selenium.webdriver.edge.options import Options as EdgeOptions  # Uncomment for Edge
from selenium.webdriver.edge.service import Service as EdgeService  # Uncomment for Edge

# from webdriver_manager.chrome import ChromeDriverManager # Assuming Chrome
from webdriver_manager.microsoft import EdgeChromiumDriverManager  # Uncomment for Edge

import csv
import os
import time
from bs4 import BeautifulSoup  # Import BeautifulSoup


def scrape_500global_portfolio():
    url = "https://500.co/portfolio"
    output_csv_path = "500global_portfolio.csv"

    # Set up Edge options for headless browsing
    edge_options = EdgeOptions()
    # edge_options.add_argument("--headless=new")
    edge_options.add_argument("--disable-dev-shm-usage")
    service = EdgeService(executable_path="C:/edgedriver_win64/msedgedriver.exe")

    # You might need to specify the executable path if webdriver_manager has issues
    # service = ChromeService(executable_path=ChromeDriverManager().install()) # For Chrome
    # driver = webdriver.Chrome(service=service, options=chrome_options)

    # For simplicity, using directly without explicit service in some versions,
    # or rely on webdriver_manager to download and manage.
    try:
        driver = webdriver.Edge(service=service, options=edge_options)
    except Exception as e:
        print(f"Error setting up Selenium WebDriver: {e}")
        print(
            "Attempting to initialize WebDriver without explicitly providing service (might work if msedgedriver is in PATH)."
        )
        driver = webdriver.Edge(options=edge_options)

    wait = WebDriverWait(driver, 20)  # Increased wait time

    print(f"Navigating to {url}...")
    try:
        driver.get(url)
        # Wait for the main content to load. The "Portfolio Companies" heading seems reliable.
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//h2[text()='Portfolio Companies']")
            )
        )
        print("Page loaded. Waiting for company cards to appear...")

        # A more general selector for company cards based on the structure observed.
        # We need to wait for at least one company card to be present.
        # The class names are dynamically generated in some parts, but the overall structure (div with certain classes) might be stable.
        # I'll use a portion of the class names that seem common.
        # Let's try waiting for an element that contains "flex p-4 flex-col-reverse"

        # Scroll to load all companies in the batch
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Give some time for new content to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Now try to find the company cards after scrolling
        # The full class string is:
        # "w-full flex p-4 flex-col-reverse md:flex-row lg:p-6 my-2 gap-3 lg:gap-0 bg-white rounded-[7px] border border-neutral-200 items-center justify-between"
        # We need to escape colons and spaces for CSS_SELECTOR or use XPATH. XPATH is probably safer for complex classes.
        company_card_selector = "//div[contains(@class, 'flex p-4 flex-col-reverse') and contains(@class, 'bg-white') and contains(@class, 'rounded-[7px]') and contains(@class, 'border')]"
        wait.until(
            EC.presence_of_all_elements_located((By.XPATH, company_card_selector))
        )
        company_cards = driver.find_elements(By.XPATH, company_card_selector)
        print("No of card_elements:", len(company_cards))

        if not company_cards:
            print(
                "No company cards found after dynamic load. Check selectors and page structure."
            )
            driver.quit()
            return

        print(f"Found {len(company_cards)} company cards.")

        scraped_data = []
        scraped_data.append(["Company Name", "Website", "LinkedIn"])  # Header row

        for i, card_element in enumerate(
            company_cards
        ):  # Renamed to card_element to avoid confusion with BeautifulSoup object
            company_name = "N/A"
            website_link = "N/A"
            linkedin_link = "N/A"

            try:
                # Parse the outerHTML of the WebElement with BeautifulSoup
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

                # Find Website Link:
                # If website_link wasn't set by the name_link, try to find another relevant link
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

                # Find LinkedIn Link:
                linkedin_link_element = card_soup.find(
                    "a", href=lambda href: href and "linkedin.com" in href
                )
                if linkedin_link_element:
                    linkedin_link = linkedin_link_element["href"]

            except Exception as e:
                print(f"Error processing card {i}: {e}")

            scraped_data.append([company_name, website_link, linkedin_link])

    finally:
        driver.quit()

    try:
        with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerows(scraped_data)
        print(f"Scraping complete. Data saved to {output_csv_path}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")


if __name__ == "__main__":
    scrape_500global_portfolio()
