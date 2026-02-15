import requests
from bs4 import BeautifulSoup
import re
from duckduckgo_search import DDGS
import warnings
from flask import Flask, request, jsonify

warnings.filterwarnings("ignore")
app = Flask(__name__)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def search_lead(first_name, last_name, company_name):
    result = {"ai_found_email": None, "source": None}
    
    # 1. Поиск личного email в Google/DDG
    query_personal = f'"{first_name} {last_name}" "{company_name}" email'
    try:
        ddg_results = DDGS().text(query_personal, max_results=3)
        for res in ddg_results:
            snippet = res.get('body', '') + " " + res.get('title', '')
            emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", snippet)
            valid_emails = [e for e in emails if not e.endswith(('png', 'jpg', 'jpeg', 'js'))]
            if valid_emails:
                result["ai_found_email"] = valid_emails[0]
                result["source"] = "Search Snippet (Personal)"
                return result
    except:
        pass

    # 2. Ищем сайт компании, если личный не найден
    query_company = f"{company_name} Cyprus official website"
    website = None
    try:
        ddg_results = DDGS().text(query_company, max_results=2)
        if ddg_results:
            for res in ddg_results:
                href = res['href']
                if not any(x in href for x in ['facebook', 'linkedin', 'instagram', 'dnb.com', 'kompass']):
                    website = href
                    break
    except:
        pass

    # 3. Парсим найденный сайт
    if website:
        try:
            response = requests.get(website, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            mailtos = soup.select('a[href^=mailto]')
            if mailtos:
                result["ai_found_email"] = mailtos[0]['href'].replace('mailto:', '').split('?')[0]
                result["source"] = f"Company Website ({website})"
                return result
                
            emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", response.text)
            valid_emails = [e for e in emails if not e.endswith(('png', 'jpg', 'js', 'css', 'gif', 'svg'))]
            if valid_emails:
                result["ai_found_email"] = valid_emails[0]
                result["source"] = f"Company Website ({website})"
                return result
        except:
            pass

    return result

@app.route('/search', methods=['GET'])
def search():
    first = request.args.get('first', '')
    last = request.args.get('last', '')
    company = request.args.get('company', '')

    if not company:
        return jsonify({"error": "Company parameter is missing"}), 400

    data = search_lead(first, last, company)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
