import os
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
import sqlite3
import boto3
import io
import tempfile

# AWS S3 setup
s3 = boto3.client('s3')
bucket_name = os.getenv("S3_BUCKET_NAME")  # Set in Lambda environment variables
db_key = "jobs.db"  # S3 object key for the database

# Configuration from Lambda environment variables
sender_email = os.getenv("JOB_SCRAPER_EMAIL")
sender_password = os.getenv("JOB_SCRAPER_PASSWORD")
receiver_email = os.getenv("JOB_SCRAPER_RECEIVER")
smtp_server = "smtp.gmail.com"
smtp_port = 587
search_terms = ["Quality Assurance Tech", "Quality Assurance Engineer", "QAT", "QAE", "Support Engineer"]
cutoff_date = datetime(2025, 4, 3)

# Check credentials
if not all([sender_email, sender_password, receiver_email, bucket_name]):
    raise ValueError("Missing environment variables: JOB_SCRAPER_EMAIL, JOB_SCRAPER_PASSWORD, JOB_SCRAPER_RECEIVER, S3_BUCKET_NAME")


def download_db_from_s3(temp_db_path):
    print(f"Attempting to download from bucket: {bucket_name}, key: {db_key}")
    try:
        s3.download_file(bucket_name, db_key, temp_db_path)
        print("Download successful")
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print("NoSuchKey: Creating new DB")
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS jobs 
                              (title TEXT, date TEXT, url TEXT UNIQUE, sent INTEGER DEFAULT 0)''')
            conn.commit()
            conn.close()
        else:
            print(f"Download failed: {str(e)}")
            raise


def upload_db_to_s3(temp_db_path):
    s3.upload_file(temp_db_path, bucket_name, db_key)


def lambda_handler(event, context):
    # Temporary file for SQLite DB
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name
        download_db_from_s3(temp_db_path)

        # Set up ChromeDriver (assumed in /opt/ for Lambda layers or package)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        service = Service(executable_path="/opt/chromedriver")  # Adjust if in package root
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Scrape jobs
            job_results = scrape_jobs(driver, temp_db_path)
            if job_results:
                send_email(job_results, temp_db_path)
            upload_db_to_s3(temp_db_path)
            return {"statusCode": 200, "body": f"Found {len(job_results)} new jobs"}
        finally:
            driver.quit()
            os.remove(temp_db_path)


def scrape_jobs(driver, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    job_results = []

    try:
        driver.get("https://www.amazon.jobs/en/")
        try:
            accept_button = driver.find_element(By.ID, "btn-accept-cookies")
            accept_button.click()
            time.sleep(1)
        except:
            pass

        for term in search_terms:
            driver.get("https://www.amazon.jobs/en/")
            time.sleep(2)
            driver.execute_script(
                "document.getElementById('search_typeahead').value = arguments[0];", term
            )
            driver.execute_script(
                "document.querySelector('.search-form').submit();"
            )
            time.sleep(7)

            while True:
                job_cards = driver.find_elements(By.CLASS_NAME, "job-tile")
                for job in job_cards:
                    try:
                        title_elem = job.find_element(By.CSS_SELECTOR, "h3.job-title a.job-link")
                        title = title_elem.text.strip()
                        if not any(t in title for t in search_terms):
                            continue
                        job_url = title_elem.get_attribute("href")
                        date_text = job.find_element(By.CSS_SELECTOR, "h2.posting-date").text.replace('Posted ', '')
                        post_date = datetime.strptime(date_text, '%B %d, %Y')
                        if post_date >= cutoff_date:
                            cursor.execute("INSERT OR IGNORE INTO jobs (title, date, url) VALUES (?, ?, ?)",
                                           (title, post_date.strftime('%Y-%m-%d'), job_url))
                            conn.commit()
                            if cursor.rowcount > 0:
                                job_results.append({
                                    "title": title,
                                    "date": post_date.strftime('%Y-%m-%d'),
                                    "url": job_url
                                })
                    except Exception as e:
                        print(f"Error processing job: {e}")
                try:
                    next_button = driver.find_element(By.CLASS_NAME, "pagination-next")
                    next_button.click()
                    time.sleep(5)
                except:
                    break
    except Exception as e:
        print(f"Scraping error: {e}")
    finally:
        conn.close()
    return job_results


def send_email(job_results, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    html_body = "<h2>New Amazon Jobs (Posted on or after April 3, 2025)</h2><ul>"
    for job in job_results:
        html_body += f'<li><a href="{job["url"]}">{job["title"]}</a> - Posted: {job["date"]}</li>'
        cursor.execute("UPDATE jobs SET sent = 1 WHERE url = ?", (job["url"],))
    html_body += "</ul>"
    conn.commit()

    msg = MIMEText(html_body, 'html')
    msg['Subject'] = "New Amazon Job Scraper Results"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
    conn.close()
