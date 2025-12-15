import requests
from bs4 import BeautifulSoup
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from .base import LLMProvider
from .gemini import GeminiProvider

class ResearcherProvider:
    def __init__(self):
        self.llm = GeminiProvider()

        # Cache configuration
        self.cache_dir = Path("cache/research")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)  # 24-hour cache

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL hash"""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cached_brief(self, url: str) -> str | None:
        """Retrieve cached brief if available and not expired"""
        cache_file = self.cache_dir / f"{self._get_cache_key(url)}.json"

        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding='utf-8'))
                cached_time = datetime.fromisoformat(data['timestamp'])

                if datetime.now() - cached_time < self.cache_ttl:
                    print(f"[RESEARCHER] Using cached data for {url} (age: {(datetime.now() - cached_time).seconds}s)")
                    return data['brief']
                else:
                    print(f"[RESEARCHER] Cache expired for {url}")
            except Exception as e:
                print(f"[RESEARCHER] Cache read error: {e}")

        return None

    def _cache_brief(self, url: str, brief: str):
        """Save brief to cache"""
        cache_file = self.cache_dir / f"{self._get_cache_key(url)}.json"
        try:
            cache_file.write_text(json.dumps({
                'url': url,
                'brief': brief,
                'timestamp': datetime.now().isoformat()
            }, indent=2), encoding='utf-8')
            print(f"[RESEARCHER] Cached brief for {url}")
        except Exception as e:
            print(f"[RESEARCHER] Cache write error: {e}")

    def _extract_content_smart(self, soup: BeautifulSoup) -> str:
        """Extract content using semantic HTML priority and noise removal"""

        # Remove noise elements
        for tag in soup(['header', 'footer', 'nav', 'aside', 'script', 'style', 'noscript', 'iframe']):
            tag.decompose()

        # Priority 1: Structured content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main', re.I))

        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            # Fallback: Get all paragraphs
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20]
            text = ' '.join(paragraphs[:15])  # First 15 substantial paragraphs

        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Extract metadata
        title = soup.find('title')
        meta_description = soup.find('meta', attrs={'name': 'description'})
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        og_title = soup.find('meta', attrs={'property': 'og:title'})

        metadata = []
        if title:
            metadata.append(f"Title: {title.get_text().strip()}")
        if og_title:
            metadata.append(f"OG Title: {og_title.get('content', '').strip()}")
        if meta_description:
            metadata.append(f"Description: {meta_description.get('content', '').strip()}")
        if og_description:
            metadata.append(f"OG Description: {og_description.get('content', '').strip()}")

        # Combine metadata + content
        combined = "\n".join(metadata) + "\n\n" + text

        # Smart truncation at sentence boundaries
        if len(combined) > 15000:
            sentences = combined[:15000].split('. ')
            if len(sentences) > 1:
                combined = '. '.join(sentences[:-1]) + '.'  # Remove partial sentence

        return combined

    def fetch_and_analyze(self, url: str) -> str:
        """
        Scrapes the URL and uses Gemini to generate a structured product brief.
        Includes 24-hour caching and smart content extraction.
        """
        # Check cache first
        cached_brief = self._get_cached_brief(url)
        if cached_brief:
            return cached_brief

        print(f"[RESEARCHER] Visiting {url}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Use smart extraction
            raw_content = self._extract_content_smart(soup)

            print("[RESEARCHER] Analyzing content with Gemini...")
            # Use Gemini to summarize into structured brief
            prompt = f"""
            You are an expert Market Researcher. Analyze the following website content for a product/service.

            Website Content:
            {raw_content[:15000]}

            Output a detailed 'Product Brief' containing:
            1. Product/Service Name
            2. Core Value Proposition (USP) - What makes it unique?
            3. Target Audience - Who is this for?
            4. Top 5 Key Features - Specific benefits or features
            5. Brand Tone - (e.g., Luxury, Playful, Professional, Technical, Friendly)
            6. Industry - Category for compliance (e.g., Healthcare, Finance, Tech, Consumer Goods)
            7. Competitors Mentioned - Any competitors referenced
            8. One-Sentence Pitch - Elevator pitch

            Format as plain text, be concise but detailed. Focus on information that would help create an effective commercial.
            """

            brief = self.llm.model.generate_content(prompt).text

            # Cache the result
            self._cache_brief(url, brief)

            return brief

        except requests.exceptions.Timeout:
            print(f"[ERROR] Researcher timeout for {url}")
            return f"Website timeout. Using URL as context: {url}"
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Researcher request failed: {e}")
            return f"Could not fetch website. Using URL as context: {url}"
        except Exception as e:
            print(f"[ERROR] Researcher failed: {e}")
            return f"Could not analyze URL. Using raw input: {url}"
