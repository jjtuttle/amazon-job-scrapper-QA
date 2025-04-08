from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText

# Set the path to your ChromeDriver
chromedriver_path = "/usr/local/bin/chromedriver"  # Adjust based on 'which chromedriver'

# Email configuration (update these)
sender_email = "james.j.tuttle@gmail.com"  # Your email
sender_password = "fiiu kxlb losn aowr"  # App-specific password if using Gmail
receiver_email = "james.j.tuttle@gmail.com"  # Your email or another recipient
smtp_server = "smtp.gmail.com"  # For Gmail; adjust for other providers
smtp_port = 587  # For Gmail TLS

# Set up Chrome WebDriver with Service
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service)

# Define search terms and cutoff date
search_terms = ["Quality Assurance Tech", "Quality Assurance Engineer"]
cutoff_date = datetime(2025, 4, 3)

try:
    # Load the Amazon Jobs page once
    driver.get("https://www.amazon.jobs/en/")
    
    # Handle cookies popup
    try:
        accept_button = driver.find_element(By.ID, "btn-accept-cookies")
        accept_button.click()
        print("Cookies popup accepted.")
        time.sleep(1)
    except Exception as e:
        print(f"No cookies popup found or error accepting: {e}")

    # Store job results
    job_results = []

    for term in search_terms:
        driver.get("https://www.amazon.jobs/en/")
        time.sleep(2)
        
        # Submit search via JavaScript
        driver.execute_script(
            "document.getElementById('search_typeahead').value = arguments[0];", term
        )
        driver.execute_script(
            "document.querySelector('.search-form').submit();"
        )
        print(f"Search submitted for '{term}' via JavaScript.")
        
        time.sleep(7)
        
        # Collect jobs across pages
        while True:
            job_cards = driver.find_elements(By.CLASS_NAME, "job-tile")
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
                        job_results.append({
                            "title": title,
                            "date": post_date.strftime('%Y-%m-%d'),
                            "url": job_url
                        })
                        print(f"Found: {title}, Posted: {post_date.strftime('%Y-%m-%d')}")
                except Exception as e:
                    print(f"Error processing job: {e}")
            
            # Check for "Next" button (adjust class/ID if needed)
            try:
                next_button = driver.find_element(By.CLASS_NAME, "pagination-next")
                next_button.click()
                time.sleep(5)
            except:
                break  # No more pages

finally:
    driver.quit()

# Send email with results
if job_results:
    # Build HTML email body
    html_body = "<h2>New Amazon Jobs (Posted on or after April 3, 2025)</h2><ul>"
    for job in job_results:
        html_body += f'<li><a href="{job["url"]}">{job["title"]}</a> - Posted: {job["date"]}</li>'
    html_body += "</ul>"

    # Create email
    msg = MIMEText(html_body, 'html')
    msg['Subject'] = "Amazon Job Scraper Results"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
else:
    print("No jobs found meeting criteria.")
    