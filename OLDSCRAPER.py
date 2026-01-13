from ddgs import DDGS
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
def validate_url(url):
    #Checks if it looks like a directory (has > 8 external links)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        #Visit the page (add timeout so script doesnt hang)
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 403:
            return False, "403 Forbidden (Anti-Bot)"
        if response.status_code != 200:
            return False, f"Status Code {response.status_code}"
        
        #Parse links
        soup = BeautifulSoup(response.text, 'html.parser')
        all_links = soup.find_all('a', href=True)

        #Count external domains
        home_domain = urlparse(url).netloc.replace('www.', '')
        external_domains = set()

        for link in all_links:
            href = link['href']

            #Ignore internal links (/careers, /about)
            if href.startswith('/') or href.startswith('#'):
                continue

            #get domain of the link for comparison
            try:
                link_domain = urlparse(href).netloc.replace('www.', '')
                #If it has a domain and its not the home_domain, it is external
                if link_domain and link_domain != home_domain:
                    #Ignore linkedin, twitter, and facebook
                    if not any(x in link_domain for x in ["linkedin", "twitter", "facebook", "instagram", "youtube"]):
                        external_domains.add(link_domain)
            except:
                continue

        #If the page has > 8 external links its probably a directory -- exclude
        if len(external_domains) > 8:
            return False, f"Too many external links ({len(external_domains)}) - Likely a listicle"
        
        return True, "Validation passed."
    
    except Exception as e:
        return False, f"Error visiting: {e}"

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
    seen_links = set()

    #Creates the search agent and automatically closes when it is done
    with DDGS() as ddgs:
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
                    results = ddgs.text(query, max_results=100)
                except Exception as e:
                    print(f"Search error: {e}")
                    continue

                if not results:
                    return []

                #Clean the data - right now its a list of dic's
                #We just want URL (href) and name (title)
                for result in results:
                    url = result['href'].lower()
                    title = result['title'].lower()

                    #First filter -
                    #Check if URL contains any blocked domains
                    if any(blocked in url for blocked in BLOCKLIST):
                        continue    #Skip this URL

                    #Check for "Listicle" titles (ex - best 10 companies)
                    if "best " in title or "top" in title:
                        continue


                    #Filter 2 - domain matching
                    #Extract actual domain
                    clean_domain = get_domain_from_url(url)
                    #get the words from the title
                    title_words = clean_title_words(title)


                    #At least on significant word from the title MUST be in the domain
                    match_found = False
                    for word in title_words:
                        if word in clean_domain:
                            match_found = True 
                            break

                    #Skip if no match found
                    if not match_found:
                        continue

                    #Success - only add if we havent seen this URL yet
                    if url not in seen_links:
                        print(f"    Verifying: {title[:30]}...", end=" ")

                        #Validate the url
                        is_valid, reason = validate_url(url)

                        if is_valid:
                            careers_page = None
                            try:
                                resp = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                                soup = BeautifulSoup(resp.text, 'html.parser')
                                careers_page = find_careers_link(url, soup)
                            except:
                                pass

                            #Determines the final link we present to the user
                            final_link = careers_page if careers_page else url
                            #Link type (leads to homepage or careers page)
                            link_type = "Direct Career Page" if careers_page else "Homepage"

                            print(f"Accepted - Careers: {careers_page}")
                            seen_links.add(url)

                            #Structure data for CSV
                            data = {
                                "Company Name": result['title'],
                                "Link": final_link,
                                "Type": link_type,
                                "Source Keyword": f"{domain} {intent}"
                            }
                            yield data


                        else:
                            print(f"Rejected: ({reason})")

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
