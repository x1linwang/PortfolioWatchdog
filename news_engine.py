import requests
from bs4 import BeautifulSoup
import numpy as np
from openai import OpenAI
from datetime import datetime

class NewsEngine:
    def __init__(self):
        self.articles = []    
        self.embeddings = []  
        self.client = OpenAI()
        
    def fetch_ap_news(self, query="Financial Markets"):
        """Scrapes AP News. Teaches HTML parsing."""
        base_url = "https://apnews.com/search"
        params = {"q": query}
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."}
        
        try:
            response = requests.get(base_url, params=params, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Note: Selectors change; this is a generic robust selector for AP
            results = soup.find_all('div', class_='PagePromo-content')
            
            new_articles = []
            for res in results[:3]: 
                title_tag = res.find('span', class_='PagePromoContentIcons-text')
                if title_tag:
                    text = title_tag.get_text(strip=True)
                    new_articles.append({"text": text, "timestamp": datetime.now().isoformat()})
            
            if not new_articles:
                return "No articles found (HTML structure might have changed). Try Google News tool."

            return self._embed_and_store(new_articles)
        except Exception as e:
            return f"Scraping Error: {e}"

    def _embed_and_store(self, articles):
        if not articles: return "No news found."
        
        texts = [a['text'] for a in articles]
        resp = self.client.embeddings.create(input=texts, model="text-embedding-3-small")
        
        for i, data in enumerate(resp.data):
            self.articles.append(articles[i])
            self.embeddings.append(data.embedding)
            
        return f"✅ Memorized {len(articles)} new articles locally."

    def search_news(self, query):
        """Retrieves using Cosine Similarity."""
        if not self.embeddings: return "Local brain is empty. Fetch news first."

        q_vec = self.client.embeddings.create(input=[query], model="text-embedding-3-small").data[0].embedding
        
        sims = []
        for i, doc_vec in enumerate(self.embeddings):
            score = np.dot(q_vec, doc_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(doc_vec))
            sims.append((score, self.articles[i]))
            
        sims.sort(key=lambda x: x[0], reverse=True)
        top_match = sims[0][1]
        return f"🔎 FOUND LOCAL MATCH: '{top_match['text']}'"