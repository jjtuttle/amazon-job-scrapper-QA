## Amazon External Job Scrapper - Quality Assurance Engineer/Tech
### This is for LOCAL use

This Python script automates job hunting on Amazon's external job search site (https://www.amazon.jobs/en/), targeting roles like "Quality Assurance Engineer" and "Quality Assurance Tech." It scrapes job listings hourly or on-demand, filters for new postings (based on a configurable cutoff date), stores results in a local SQLite database, and emails new jobs using your configured email settings. Ideal for engineers seeking QA-related opportunities at Amazon.

### Features

- **Scheduled Scraping:** Runs every hour by default to check for new job postings.
- **On-Demand Execution:** Trigger manually via a simple CLI (run command).
- **Persistent Storage:** Tracks jobs in a SQLite database, using a sent flag to avoid duplicate emails.
- **Customizable Search:** Predefined search terms (Quality Assurance Tech, Quality Assurance Engineer, QAT, QAE, Hardware) with easy CLI additions.
- **Email Notifications:** Sends HTML emails with hyperlinked job titles for new postings.
- **Learning Potential:** Tracks term frequency to suggest focus areas ( extensible for future enhancements).

### Prerequisites

- **Python 3.8+:** Ensure Python is installed (`python3 --version`).
- **ChromeDriver:** Compatible with your installed Chrome version (download from chromedriver.chromium.org).
- **Dependencies:** Install required Python libraries (see ).
- **Email Account:** A sender email with an app-specific password (e.g., Gmail with 2FA enabled).

## Installation - LOCAL

1. **Clone the Repository:**

```
git clone https://github.com/yourusername/amazon-job-scraper.git
cd amazon-job-scraper
```

2. **Install Dependencies:**

```
  pip3 install selenium schedule
```

3. **Set Up ChromeDriver:**

- Place `chromedriver` in `/usr/local/bin/` (or update `chromedriver_path` in the script).
- Verify: `which chromedriver`.

4. **Configure Environment Variables:** Set these variables for email functionality:

```
export JOB_SCRAPER_EMAIL="your_email@gmail.com"
export JOB_SCRAPER_PASSWORD="your_app_password"
export JOB_SCRAPER_RECEIVER="recipient_email@example.com"
export JOB_SCRAPER_DB_PATH="/path/to/your/jobs.db"  # Optional, defaults to "jobs.db" in current directory
```

- For persistence, add to `~/.zshrc` (or equivalent) and run `source ~/.zshrc`.
- Note: Use an app-specific password if your email provider requires 2FA (e.g., [Google App Passwords](https://myaccount.google.com/apppasswords)).

## Usage

1. **Run the Script:**

```
python3 amazon_jobs_scraper_agent_V2.py
```

- Starts the agent, running hourly in the background.
- Displays: `Starting AI Job Scraper Agent... Agent>`.

2. **Interact via CLI:**

- `run`: Scrape and email new jobs immediately.
- `interval <hours>`: Change the run frequency (e.g., interval 2 for every 2 hours).
- `add <term>`: Add a new search term (e.g., add Software).
- `suggest`: View term frequency and suggestions.
- `quit`: Exit the agent.

3. **Output:**

- New jobs are stored in jobs.db and emailed with hyperlinked titles.
- Console logs show scraping progress and term frequency.

## Configuration

- **Search Terms**: Edit `search_terms` in the script or use `add <term>`:

```
search_terms = ["Quality Assurance Tech", "Quality Assurance Engineer", "QAT", "QAE", "Hardware"]
```

- **Cutoff Date**: Modify `cutoff_date` for job freshness:

```
cutoff_date = datetime(2025, 4, 3)
```

- **Database**: SQLite schema (jobs.db):

```
- title (TEXT): Job title
- date (TEXT): Posting date (YYYY-MM-DD)
- url (TEXT, UNIQUE): Job URL
- sent (INTEGER): 0 = not emailed, 1 = emailed
```

## Example

```
$ python3 amazon_jobs_scraper_agent_V2.py
Starting AI Job Scraper Agent...
Agent> run
Search submitted for 'Quality Assurance Tech'.
Search submitted for 'Quality Assurance Engineer'.
New job found: Quality Assurance Engineer, Posted: 2025-04-03
Email sent successfully!
Run completed at 2025-04-04 17:00:00
Search term frequency: {'Quality Assurance Engineer': 1}
Suggested focus term: Quality Assurance Engineer
Agent>
```

### Email received:

<img width="600" alt="Screenshot 2025-04-08 at 10 27 56 AM" src="https://github.com/user-attachments/assets/743c5787-ca12-4989-93df-3a4378d1374d" />
<hr />

### Notes

- **Thread Safety:** SQLite connections are thread-local to avoid conflicts.
- **Headless Mode:** Runs ChromeDriver in headless mode for background execution.
- **Security:** Credentials are loaded from environment variables, not hardcoded.

### Contributing

**_Feel free to fork, submit pull requests, or open issues for enhancements (e.g., LLM integration, multi-site scraping)._**
