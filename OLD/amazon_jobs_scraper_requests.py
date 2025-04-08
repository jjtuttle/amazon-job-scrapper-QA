import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Define URL and headers
base_url = "https://www.amazon.jobs/en/search?base_query="
search_terms = ["Quality+Assurance+Tech", "Quality+Assurance+Engineer"]
cutoff_date = datetime(2025, 4, 1)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
}

def scrape_jobs(search_term):
    url = f"{base_url}{search_term}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {url}. Status: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    job_cards = soup.select('.job-tile')
    jobs = []
    
    for job in job_cards:
        title_elem = job.select_one('h3.job-title a.job-link')
        title = title_elem.text.strip() if title_elem else "No title"
        
        if not any(term.replace('+', ' ') in title for term in search_terms):
            continue
        
        date_elem = job.select_one('h2.posting-date')
        date_text = date_elem.text.strip().replace('Posted ', '') if date_elem else "Unknown"
        
        try:
            post_date = datetime.strptime(date_text, '%B %d, %Y')
            if post_date >= cutoff_date:
                jobs.append({"title": title, "date": post_date.strftime('%Y-%m-%d')})
        except ValueError:
            continue
    
    return jobs

# Run for each search term
for term in search_terms:
    print(f"\nSearching for: {term.replace('+', ' ')}")
    job_listings = scrape_jobs(term)
    for job in job_listings:
        print(f"Title: {job['title']}, Posted: {job['date']}")