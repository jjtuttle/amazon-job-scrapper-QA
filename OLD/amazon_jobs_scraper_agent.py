#!/usr/bin/env python3

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import time
import smtplib
from email.mime.text import MIMEText
import sqlite3
import schedule
import threading
import sys

# Configuration
chromedriver_path = "/usr/local/bin/chromedriver"
# Email configuration
sender_email = "james.j.tuttle@gmail.com" 
sender_password = "fiiu kxlb losn aowr"  
receiver_email = "james.j.tuttle@gmail.com"  
smtp_server = "smtp.gmail.com" 
smtp_port = 587  # For Gmail TLS
# Search terms
search_terms = ["Quality Assurance Tech", "Quality Assurance Engineer"]
# Cutoff date
cutoff_date = datetime(2025, 4, 3)

# Database setup
conn = sqlite3.connect("/Users/jamestuttle/_Projects/tuttle/web_scraper/jobs.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS jobs 
                  (title TEXT, date TEXT, url TEXT UNIQUE, sent INTEGER DEFAULT 0)''')
conn.commit()

# AI Agent class
class JobScraperAgent:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        self.last_run = None
        self.run_interval = 3600  # Default: 1 hour in seconds

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run headless for background execution
        service = Service(executable_path=chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=options)

    def scrape_jobs(self):
        job_results = []
        try:
            self.driver.get("https://www.amazon.jobs/en/")
            try:
                accept_button = self.driver.find_element(By.ID, "btn-accept-cookies")
                accept_button.click()
                print("Cookies popup accepted.")
                time.sleep(1)
            except:
                pass  # Popup might not appear in headless mode

            for term in search_terms:
                self.driver.get("https://www.amazon.jobs/en/")
                time.sleep(2)
                self.driver.execute_script(
                    "document.getElementById('search_typeahead').value = arguments[0];", term
                )
                self.driver.execute_script(
                    "document.querySelector('.search-form').submit();"
                )
                print(f"Search submitted for '{term}'.")
                time.sleep(7)

                while True:
                    job_cards = self.driver.find_elements(By.CLASS_NAME, "job-tile")
                    for job in job_cards:
                        try:
                            title_elem = job.find_element(By.CSS_SELECTOR, "h3.job-title a.job-link")
                            title = title_elem.text.strip()
                            if not any(search_term in title for search_term in search_terms):
                                continue
                            job_url = title_elem.get_attribute("href")
                            date_text = job.find_element(By.CSS_SELECTOR, "h2.posting-date").text.replace('Posted ', '')
                            post_date = datetime.strptime(date_text, '%B %d, %Y')
                            if post_date >= cutoff_date:
                                # Check if job is new
                                cursor.execute("INSERT OR IGNORE INTO jobs (title, date, url) VALUES (?, ?, ?)",
                                               (title, post_date.strftime('%Y-%m-%d'), job_url))
                                conn.commit()
                                if cursor.rowcount > 0:  # New job inserted
                                    job_results.append({
                                        "title": title,
                                        "date": post_date.strftime('%Y-%m-%d'),
                                        "url": job_url
                                    })
                        except Exception as e:
                            print(f"Error processing job: {e}")
                    try:
                        next_button = self.driver.find_element(By.CLASS_NAME, "pagination-next")
                        next_button.click()
                        time.sleep(5)
                    except:
                        break
        except Exception as e:
            print(f"Scraping error: {e}")
            self.restart_driver()
        return job_results

    def send_email(self, job_results):
        if not job_results:
            return
        html_body = f'<h2>New Amazon Jobs (Posted on or after {cutoff_date})</h2><ul>'
        for job in job_results:
            html_body += f'<li><a href="{job["url"]}">{job["title"]}</a> - Posted: {job["date"]}</li>'
            cursor.execute("UPDATE jobs SET sent = 1 WHERE url = ?", (job["url"],))
        html_body += "</ul>"
        conn.commit()

        msg = MIMEText(html_body, 'html')
        msg['Subject'] = "Amazon Job Scraper Results"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")

    def restart_driver(self):
        if self.driver:
            self.driver.quit()
        self.setup_driver()

    def run(self):
        jobs = self.scrape_jobs()
        if jobs:
            self.send_email(jobs)
        self.last_run = datetime.now()
        print(f"Run completed at {self.last_run}")

    def schedule_task(self):
        schedule.every(self.run_interval // 3600).hours.do(self.run)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def interactive_loop(self):
        while True:
            command = input("Agent> ").strip().lower()
            if command == "run":
                self.run()
            elif command.startswith("interval "):
                try:
                    new_interval = int(command.split()[1]) * 3600  # Convert hours to seconds
                    self.run_interval = new_interval
                    schedule.clear()
                    schedule.every(self.run_interval // 3600).hours.do(self.run)
                    print(f"Interval set to {self.run_interval // 3600} hours.")
                except:
                    print("Invalid interval. Use: interval <hours>")
            elif command == "quit":
                break
            else:
                print("Commands: run, interval <hours>, quit")

# Run the agent
agent = JobScraperAgent()
print("Starting AI Job Scraper Agent...")
print(f"Commands: run, interval <hourly>, quit")

# Run in background thread
threading.Thread(target=agent.schedule_task, daemon=True).start()

# Interactive CLI
agent.interactive_loop()

# Cleanup
agent.driver.quit()
conn.close()
