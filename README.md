# YCScraper: Y-Combinator Founder Social Link Scraper (LinkedIn & X.com)

## 🚀 Overview
YCScraper is a powerful and efficient Python-based tool designed to automatically scrape and collect public LinkedIn and X.com (formerly Twitter) profiles of founders from Y-Combinator (YC)-backed companies. Whether you're a recruiter, investor, researcher, or simply looking to expand your network within the startup ecosystem, YCScraper provides an invaluable resource for data extraction and analysis.

This project leverages browser automation to navigate YC's extensive company directory and meticulously extract founder information, presenting it in a clean, structured format for easy use.

## ✨ Features
*   **Comprehensive Data Collection:** Gathers LinkedIn and X.com URLs for Y-Combinator founders.
*   **Automated Browsing:** Utilizes Selenium for robust web scraping, handling dynamic content.
*   **Configurable:** Easily adaptable for different YC batches or specific company lists.
*   **Structured Output:** Generates CSV files with founder names, company affiliations, and their respective social media links.
*   **Developer-Friendly:** Written in Python, making it easy to understand, modify, and extend.

## 🛠️ Technologies Used
*   **Python 3.x:** The core programming language.
*   **Selenium:** For browser automation and web interaction.
*   **WebDriver Manager:** To automatically manage and download appropriate browser drivers (e.g., ChromeDriver).

## ⚡ Getting Started

### Prerequisites
Before you begin, ensure you have the following installed:
*   Python 3.x
*   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/YCScraper.git
    cd YCScraper
    ```
    *(Note: Replace `your-username` with the actual GitHub username or the repository URL if different.)*

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate   # On Windows
    source venv/bin/activate # On macOS/Linux
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

### Usage

To run the scraper, simply execute the main Python script:

```bash
python YCScraper.py
```

The script will automatically launch a browser, navigate through the YC company pages, and extract the founder social links. Once completed, the data will be saved into a CSV file (e.g., `yc_founders_social.csv` or `yc_founders_social_old.csv` based on project files) in the root directory of the project.

### Output Example
The generated CSV file will typically have columns similar to this:

| Company Name        | Founder Name     | LinkedIn Profile                               | X.com Profile                           |
| :------------------ | :--------------- | :--------------------------------------------- | :-------------------------------------- |
| Example Startup Inc. | Jane Doe         | `https://www.linkedin.com/in/janedoe`          | `https://x.com/janedoe`                 |
| Innovative Solutions | John Smith       | `https://www.linkedin.com/in/johnsmith`        | `https://x.com/johnsmith_tech`          |
| ...                 | ...              | ...                                            | ...                                     |

## 🤝 Contributing
Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please feel free to:
1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the `LICENSE` file for details.
*(Note: A `LICENSE` file should be added to the repository if not already present.)*
