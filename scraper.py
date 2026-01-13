from duckduckgo_search import DDGS
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests
import json
import re
import time
import random
import csv


#These are domains that clutter results but arent actual companies.
BLOCKLIST = [
    #Aggregators & Directories
    "yelp", "mapquest", "chamberofcommerce", "yellowpages", 
    "zippia", "glassdoor", "linkedin", "indeed", "facebook", 
    "instagram", "twitter", "opengovny", "timesunion", 
    "zoominfo", "dnb", "manta", "bbb.org", "bizjournals", 
    "alignable", "redshiftrecruiting", "renscochamber",
    "simplyhired", "monster", "careerbuilder", "jobs2careers", 
    "talroo", "upwork", "fiverr", "thumbtack", "bark",
    #Student/Academic Sites (The "WayUp" Fix)
    "wayup", "handshake", "chegg", "coursehero", "varsitytutors",
    "superprof", "wyzant", "udemy", "coursera", "ratemyprofessors"
]

#Extracts the domain from a URL
def get_domain_from_url(url):
    #Input: https://www.website.com/careers
    #Output: website
    try:
        parsed = urlparse(url)

        #get domain
        domain = parsed.netloc
        #remove www. if present
        if domain.startswith("www."):
            domain = domain[4:]
        #remove extension
        if "." in domain:
            domain = domain.split('.')[0]
        return domain.lower()
    except:
        return ""

#Breaks title into a list of significant words
def clean_title_words(title):
    #Input: Gavant Software | Custom Dev
    #Output: ['gavant', 'software', 'custom', 'dev']
    title = title.lower()
    clean_text = re.sub(r'[^a-z\s]', ' ', title)
    words = clean_text.split()

    #remove generic filler words
    stop_words = {'home', 'welcome', 'inc', 'llc', 'company', 'corporation', 'about', 'contact', 'profile'}
    return [w for w in words if w not in stop_words and len(w) > 2]

#Validates a url to be a company page or not (removes listicles)
def validate_page_content(url, soup):
    try:
        #block "Top 10" Listicles
        title = soup.title.string.lower() if soup.title else ""
        if any(x in title for x in ["best", "top 10", "rankings", "directory"]):
            return False, "Likely a listicle"

        #content Check (Must have business words)
        text = soup.get_text().lower()
        signals = ["services", "clients", "about us", "contact", "products", "solutions"]
        if sum(1 for s in signals if s in text) < 2:
            return False, "Not enough business content"

        #link Density Check (Aggregators have too many external links)
        links = soup.find_all('a', href=True)
        external = sum(1 for l in links if 'http' in l['href'] and urlparse(url).netloc not in l['href'])
        if external > 50: return False, "Too many external links"

        return True, "Valid"
    except: return False, "Validation Error"

#finds the career/jon posting page of the website
def find_careers_link(url, soup):
    try:
        #keywords
        keywords = ["career", "job", "join", "opportunity", "work with us", "hiring"]

        #check all links on the page
        for link in soup.find_all('a', href = True):
            text = link.get_text().lower()
            href = link['href']

            #if any link contains a keyword - get that link
            if any(keyword in text for keyword in keywords):
                return urljoin(url, href)
            
        return None
    except:
        return None

#Does a search for each keyword given and combines the results
def scrape(city, domains, intents):
    #Gets company urls with one keyword and a city given
    print(f"Searching for overlaps in {city}...")

    #To prevent duplicates between keyword searches
    seen_urls = set()

    #Proxy used from webshare
    PROXY = "https://phojmtmo:y14gw6197pqb@142.111.48.253:7030"
    print(f"Connecting via proxy: {PROXY}")

    #Creates the search agent and automatically closes when it is done
    with DDGS(proxy=PROXY) as ddgs:
        #loop 1: the domain - eg "Machine Learning"
        for domain in domains:
            #loop 2: the intent - eg "Internship"
            for intent in intents:
                print(f"Checking keyword: '{domain} {intent}'")

                #Build query based off of these keyword(s)
                query = f'"{domain} {intent}" "{city}" site:.com -site:linkedin.com -site:indeed.com'
                #This only searches for company homepages and excludes linkedin/indeed postings

                #text(
                #query: str (text search query)
                #region: str = "us-en" (default is us-en, could be uk-en, ru-ru, etc.)
                #safesearch: str = on, moderate, off (default is moderate)
                #timelimit: str (d, w, m, y. Default is None)
                #max_results: int (max number of results. default is 10)
                #page: int (page of results. default is 1)
                #backend: str = "auto" (single or comma-delimited backends. default to auto)
                #) --> list[dict[str, str]]

                #Returns a list of dictionaries with the search results
                try:
                    results = ddgs.text(query, backend="lite", max_results=25)
                except Exception as e:
                    print(f"Search error: {e}")
                    continue

                if not results:
                    continue

                #Clean the data - right now its a list of dic's
                #We just want URL (href) and name (title)
                for result in results:
                    url = result['href']
                    title = result['title']
                    
                    if any(b in url for b in BLOCKLIST): continue
                    if url in seen_urls: continue
                    seen_urls.add(url)

                    try:
                        # 1. Fetch Page FIRST
                        print(f"   Checking: {title[:30]}...", end="")
                        resp = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                        if resp.status_code != 200: continue
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        
                        # 2. Validate Content
                        is_valid, reason = validate_page_content(url, soup)
                        
                        if is_valid:
                            careers = find_careers_link(url, soup)
                            data = {
                                "Company Name": title,
                                "Link": careers if careers else url,
                                "Type": "Direct Career Page" if careers else "Homepage",
                                "Source Keyword": f"{domain} ({intent})"
                            }
                            print("ACCEPTED")
                            yield data
                        else:
                            print(f"({reason})")

                    except Exception as e:
                        print(f"Error")

                    #sleep to avoid IP ban
                    time.sleep(random.uniform(1.5, 3.0))




#Testing purposes
'''
testCity = "Troy, NY"
#The what (technial field or industry)
search_domains = ["software", "web development"]
#The type (what are you looking for?)
search_intents = ["company", "agency", "firm"]
#Running function
companies = scrape(testCity, search_domains, search_intents)

#Save to CSV file
if companies:
    filename = "internship_leads.csv"
    print(f"\nFound {len(companies)} companies! Saving to '{filename}'...")

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        #get headers from first result
        writer = csv.DictWriter(f, fieldnames=companies[0].keys())
        writer.writeheader()
        writer.writerows(companies)

    print("Done.")
else:
    print("\nNo results found.")
'''
