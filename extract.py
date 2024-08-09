#! /usr/bin/python3.10

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
import pandas as pd
from datetime import datetime
from time import sleep


now = datetime.now()
date_time_format = now.strftime("%Y%m%d_%H%M%S")
output_filename = f"li_data_{date_time_format}.csv"

save_directory = f"~/scrapers/scraped_data/linkedin/{output_filename}"

ignore_companies = [
    "minware",
    "HireMeFast LLC",
    "SynergisticIT",
    "Get It Recruit - Information Technology",
    "Team Remotely Inc",
    "Dice",
    "Actalent",
    "Patterned Learning Career",
    "Sky Recruitment LLC",
    "Fitness Matrix Inc",
    "Outco Inc",
    "HireMeFast",
    "Phoenix Recruitment",
    "TEKsystems",
    "RemoteWorker US",
    "Accenture Federal Services",
    "Jobot",
    "Crossover",
    "Esyconnect",
    "RemoteWorker UK",
    "Jobot Consulting"
]

def scrape_linkedin_jobs(keyword, num_pages):

    results = pd.DataFrame(
        columns=[
            "company_name",
            "job_title",
            "extracted_skills",
            "job_link",
            "job_description",
            "date_scraped"
        ]
    )

    options = Options()
    options.add_argument("--headless") 
    
    chrome_driver_path = '/usr/local/bin/chromedriver-linux64/chromedriver'
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)


    # for entry-level:  "f_E=2"
    # for remote: "f_WT=2"
    # &f_E=1%2C2%2C3&f_WT=2&
    # posted within 24 hours: f_TPR=r86400
    extra_param = "f_E=1%2C2%2C3&f_TPR=r2592000&f_WT=2&f_TPR=r86400"
    url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&{extra_param}"
    
    print(f"Scraping from: {url}")
    
    driver.get(url)

    j = 0
    # Scroll to load more jobs (you may need to adjust the number of scrolls)
    for _ in range(num_pages):
        print("scroll ######",j)
        j = j+1
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        sleep(60)
    
    
    
    

    job_cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
    for card in job_cards:
        try:

            job_title_element = WebDriverWait(card, 60).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".base-search-card__title")
                )
            )
            company_element = WebDriverWait(card, 60).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".base-search-card__subtitle")
                )
            )
            description = WebDriverWait(card, 60).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".base-card__full-link")
                )
            )

            company_name = company_element.text

            if company_name.lower() in list(map(str.lower, ignore_companies)):
                continue

            job_title = job_title_element.text
            job_link = description.get_attribute("href")

            job_driver = webdriver.Chrome(options=options)
            job_driver.get(job_link)

            expand_description(job_driver)
            job_description = extract_job_description(job_driver)
            extracted_skills = extract_skills(job_description)

            print(f"Job Title: {job_title}, Company: {company_name}")

            results = results._append(
                {
                    "company_name": company_name,
                    "job_title": job_title,
                    "job_link": job_link,
                    "job_description": job_description,
                    "extracted_skills": extracted_skills,
                    "date_scraped": now,
                },
                ignore_index=True,
            )
            job_driver.quit()

        except Exception as e:
            print(e)
            continue

    driver.quit()

    return results


def extract_job_description(driver):
    try:
        WebDriverWait(driver, 100).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".description"))
        )

        job_description = driver.execute_script(
            "return document.querySelector('.description').textContent"
        )

        job_description = job_description.strip()
        job_description = job_description.replace("\n", "  ")
        job_description = job_description.replace("\r", "  ")
        job_description = job_description.replace("\t", "  ")
        job_description = " ".join(job_description.split())

        return job_description
    except TimeoutException:
        return ""

def expand_description(driver):
    try:
        show_more_button = WebDriverWait(card, 60).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".show-more-less-html__button")
            )
        )

        show_more_button.click()
        time.sleep(100)
    except Exception as e:
        pass 


def extract_skills(description):
    skills = [
        "PostgreSQL",
        "Airflow",
        "Python",
        "JavaScript",
        "TypeScript",
        "SQL",
        "Flask",
        "Django",
        "Nix",
        "React"
    ]
    description = description.lower()
    skills_list = [skill for skill in skills if skill.lower() in description]
    return skills_list


# Main function
if __name__ == "__main__":
    keyword = "software%20engineer"
    num_pages = 2
    print("Starting LinkedIn scraper.")
    scraped_jobs = scrape_linkedin_jobs(keyword, num_pages)
    scraped_jobs.to_csv(save_directory, index=False)
    print("Ending LinkedIn scraper")
