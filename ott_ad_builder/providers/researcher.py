import requests
from bs4 import BeautifulSoup
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

class ResearcherProvider:
    def __init__(self):
        # Cache configuration
        self.cache_dir = Path("cache/research")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)  # 24-hour cache

    def _fetch_via_jina_reader(self, url: str) -> str | None:
        """
        Fallback extractor using Jina AI Reader (free) for sites that are:
        - JS-heavy (little static HTML)
        - blocked (403/anti-bot)
        - noisy (hard to isolate main content)

        Reader format: https://r.jina.ai/https://example.com
        """
        try:
            normalized = (url or "").strip()
            if not normalized:
                return None
            # Jina expects a full URL including scheme.
            if not normalized.lower().startswith(("http://", "https://")):
                normalized = f"https://{normalized}"

            reader_url = f"https://r.jina.ai/{normalized}"
            print(f"[RESEARCHER] Fallback (Jina Reader) {reader_url}...")
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(reader_url, headers=headers, timeout=20)
            response.raise_for_status()
            text = (response.text or "").strip()
            if len(text) < 200:
                return None

            # Keep payload size bounded and sentence-safe-ish.
            if len(text) > 15000:
                text = text[:15000]
                last_period = text.rfind(". ")
                if last_period > 2000:
                    text = text[: last_period + 1]

            return f"Source URL: {normalized}\n\n{text}"
        except Exception as e:
            print(f"[RESEARCHER] Jina Reader failed: {e}")
            return None

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

    def fetch_and_extract(self, url: str) -> str:
        """
        Scrapes the URL and returns extracted on-page text (no LLM call).
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
            # If the site is JS-heavy, this can be near-empty. Trigger fallback.
            if len(raw_content) < 400:
                raise ValueError("Static HTML extraction too short; likely JS-rendered or blocked.")
            extracted = f"Source URL: {url}\n\n{raw_content}"

            # Cache the result
            self._cache_brief(url, extracted)

            return extracted

        except requests.exceptions.Timeout:
            print(f"[ERROR] Researcher timeout for {url}")
            fallback = self._fetch_via_jina_reader(url)
            if fallback:
                self._cache_brief(url, fallback)
                return fallback
            return f"Website timeout. Using URL as context: {url}"
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Researcher request failed: {e}")
            fallback = self._fetch_via_jina_reader(url)
            if fallback:
                self._cache_brief(url, fallback)
                return fallback
            return f"Could not fetch website. Using URL as context: {url}"
        except Exception as e:
            print(f"[ERROR] Researcher failed: {e}")
            fallback = self._fetch_via_jina_reader(url)
            if fallback:
                self._cache_brief(url, fallback)
                return fallback
            return f"Could not analyze URL. Using raw input: {url}"

    # Backwards-compatible alias (older code called this)
    def fetch_and_analyze(self, url: str) -> str:
        return self.fetch_and_extract(url)
