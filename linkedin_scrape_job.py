#! /usr/bin/python3.10

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from collections import Counter

import time
import pandas as pd
from datetime import datetime
from time import sleep


now = datetime.now()
date_time_format = now.strftime("%Y%m%d_%H%M%S")
output_filename = f"li_data_{date_time_format}.csv"

save_directory = f"/home/cjw/scraped_data/linkedin/{output_filename}"


# Function to scrape LinkedIn job postings and extract skills
def scrape_linkedin_jobs(keyword, num_pages):

    results = pd.DataFrame(
        columns=[
            "company_name",
            "job_title",
            "job_link",
            "job_description",
            "extracted_skills",
            "date_scraped",
        ]
    )

    # Set up options for the Chrome WebDriver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")

    # Start a Selenium WebDriver with options
    driver = webdriver.Chrome(options=options)

    # for entry-level:  "f_E=2"
    # for remote: "f_WT=2"
    # &f_E=1%2C2%2C3&f_WT=2&
    extra_param="f_E=1%2C2%2C3&f_TPR=r2592000&f_WT=2"
    url = (
        f"https://www.linkedin.com/jobs/search/?keywords={keyword}&{extra_param}"
    )
    driver.get(url)
    # j = 0
    # # Scroll to load more jobs (you may need to adjust the number of scrolls)
    # for _ in range(num_pages):
    #     # print("scroll ######", j)
    #     j = j + 1
    #     driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
    #     sleep(5)  # Wait for content to load
    
    scroll_down(driver, 5)

    # Extract job titles and skills (modify as needed)
    job_cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
    # break_element = 0
    for card in job_cards:
        try:

            job_title_element = WebDriverWait(card, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".base-search-card__title")
                )
            )
            company_element = WebDriverWait(card, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".base-search-card__subtitle")
                )
            )
            description = WebDriverWait(card, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".base-card__full-link")
                )
            )

            company_name = company_element.text
            job_title = job_title_element.text
            # print(job_title, " ", company_name)
            job_link = description.get_attribute("href")
            # print(job_link)

            # Hitting each job's URL to get more information
            job_driver = webdriver.Chrome(options=options)
            job_driver.get(job_link)

            # expand descriptions by clicking on show more
            expand_description(job_driver)
            # extract description element
            job_description = extract_job_description(job_driver)
            # extract skills from description
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
            # print("Job details not found for this card.")
            continue

    # Close the WebDriver when done
    driver.quit()

    return results


# Function to extract job description using JavaScript
def extract_job_description(driver):
    try:
        # Wait for the job description element to be present (you can adjust the timeout)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".description"))
        )

        # Execute JavaScript code to extract job description
        job_description = driver.execute_script(
            "return document.querySelector('.description').textContent"
        )

        job_description = job_description.strip()
        job_description = job_description.replace("\n", " ")
        job_description = job_description.replace("\r", " ")
        job_description = job_description.replace("\t", " ")
        job_description = " ".join(job_description.split())

        return job_description
    except TimeoutException:
        return "Job description not found or couldn't be loaded"


# Function to expand job description by clicking "show more" if available
def expand_description(driver):
    try:
        show_more_button = WebDriverWait(card, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".show-more-less-html__button")
            )
        )

        show_more_button.click()
        time.sleep(5)  # Wait for the description to expand
    except Exception as e:
        pass  # No "show more" button found or error occurred


# Function to extract skills from a job title
def extract_skills(description):
    # This is a basic example, you can extend this to match more skills
    skills = [
        "PostgreSQL",
        "Airflow",
        "Python",
        "JavaScript",
        "SQL",
        "Flask",
        "Django",
        "Nix",
    ]
    description = description.lower()
    skills_list = [skill for skill in skills if skill.lower() in description]
    return skills_list


def scroll_down(driver, scroll_delay):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        new_height = driver.execute_script("return document.body.scrollHeight")
        sleep(scroll_delay)

        if new_height == last_height:
            break
        last_height = new_height


# Main function
if __name__ == "__main__":
    keyword = "software%20engineer"
    num_pages = 1  # You can adjust the number of pages to scrape

    print("Starting LinkedIn scraper.")
    scraped_jobs = scrape_linkedin_jobs(keyword, num_pages)
    
    print(scraped_jobs)
    
    scraped_jobs.to_csv(save_directory, index=False)

    # flattened_skills = [skill for sublist in scraped_jobs for skill in sublist]
    # skill_counts = Counter(flattened_skills)
    # top_skills = skill_counts.most_common(30)

    # for skill, count in top_skills:
    #     print(f"{skill}: {count}")
