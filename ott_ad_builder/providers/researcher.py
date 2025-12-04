import requests
from bs4 import BeautifulSoup
from .base import LLMProvider
from .gemini import GeminiProvider

class ResearcherProvider:
    def __init__(self):
        self.llm = GeminiProvider()

    def fetch_and_analyze(self, url: str) -> str:
        """
        Scrapes the URL and uses Gemini to generate a structured product brief.
        """
        print(f"🕵️‍♀️ Researcher: Visiting {url}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract key elements
            title = soup.title.string if soup.title else "No Title"
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc['content'] if meta_desc else "No Description"
            
            # Get main text (rough approximation)
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            main_text = "\n".join(paragraphs[:10]) # First 10 paragraphs to avoid footer junk
            
            raw_content = f"Title: {title}\nDescription: {description}\nContent: {main_text}"
            
            print("🧠 Researcher: Analyzing content with Gemini...")
            # Use Gemini to summarize raw HTML into a clean brief
            prompt = f"""
            You are an expert Market Researcher. Analyze the following website content for a product/service.
            
            Raw Content:
            {raw_content[:10000]} # Truncate to avoid token limits
            
            Output a concise 'Product Brief' containing:
            1. Product Name
            2. Core Value Proposition (USP)
            3. Target Audience
            4. Key Features
            5. Brand Vibe (e.g., Luxury, Playful, Tech)
            6. Industry (for compliance checks)
            
            Format as plain text.
            """
            
            brief = self.llm.model.generate_content(prompt).text
            return brief
            
        except Exception as e:
            print(f"❌ Researcher Failed: {e}")
            return f"Could not scrape URL. Using raw input: {url}"
