from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
import json
import requests
import scraper
import time
import random
import logging
from datetime import datetime

app = Flask(__name__)
#allows frontend to talk to this backend
CORS(app)


KEYWORD_CACHE = {}
#This uses ConceptNet to get related terms to the given term (allows for more complex searches)
def get_related_terms(term):
    term = term.lower().strip()
    if term in KEYWORD_CACHE: return KEYWORD_CACHE[term]

    print(f"Asking ConceptNet about '{term}'...")
    related = set([term]) #always include original

    try:
        url = f"http://api.conceptnet.io/c/en/{term.replace(' ', '_')}?limit=20"
        resp = requests.get(url, timeout=2).json()
        
        for edge in resp.get('edges', []):
            try:
                if edge['end']['language'] != 'en' or edge['start']['language'] != 'en': continue
                if edge['weight'] < 1.0: continue
                
                label = edge['end']['label']
                if len(label.split()) <= 3: # Keep it short
                    related.add(label.lower())
            except: continue
    except Exception as e:
        print(f"ConceptNet error: {e}")
    
    final = list(related)[:6] # Limit to 6 terms
    KEYWORD_CACHE[term] = final
    return final



@app.route('/')
def home():
    return "Scraper API is running!"

#setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#User "searches" which sends POST info
@app.route('/api/search', methods=['POST'])
def search_companies():
    #Get data from the frontend
    data = request.json
    #Defaults if nothing is provided (software -- troy)
    city = data.get('city', 'Troy, NY')

    #get user IP
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    #log the activity
    log_message = f"USER_ACTION: IP={user_ip} | City={city} | Domains={data.get('domains')} | Time={datetime.now()}"
    #print to the local terminal and the Render dashboard
    print(log_message)
    logger.info(log_message)

    raw_domains = data.get('domains', ["software"])
    
    #expand Keywords using ConceptNet
    final_keywords = set()
    for d in raw_domains:
        final_keywords.update(get_related_terms(d))
        time.sleep(random.uniform(1.0, 1.5))
    
    search_terms = list(final_keywords)
    
    #universal Intents (Works for 95% of businesses)
    intents = ["company", "agency", "firm", "services", "studio", "group"]



    print(f"Received request for {city}...")

    def generate():
        #loop through the scrapers yields
        for company in scraper.scrape(city, search_terms, intents):
            #send one JSON object per line
            yield json.dumps(company) + "\n"
        
    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')


if __name__ == '__main__':
    #run server locally for testing
    app.run(debug=True, port=5000)



