"""
Style Detection System for Adaptive Prompt Engineering
Analyzes user input to determine creative intent and route to appropriate templates.
"""

from typing import Dict, List, Optional, Tuple
import re


class StyleDetector:
    """
    Detects creative style intent from user input and constraints.

    Returns style profile with:
    - aesthetic: Visual style category
    - format: Commercial format type
    - tone: Emotional/narrative tone
    - pacing: Timing and rhythm preferences
    - confidence: Detection confidence score (0-1)
    """

    # Style keywords for detection
    AESTHETIC_KEYWORDS = {
        "photorealistic": ["photorealistic", "realistic", "authentic", "real", "natural", "cinema", "film"],
        "abstract": ["abstract", "surreal", "dream", "conceptual", "symbolic", "metaphor", "artistic"],
        "minimalist": ["minimal", "clean", "simple", "sparse", "negative space", "zen", "pure"],
        "maximalist": ["maximal", "rich", "detailed", "complex", "ornate", "layered", "busy"],
        "noir": ["noir", "dark", "shadow", "high contrast", "black and white", "dramatic lighting"],
        "neon": ["neon", "cyberpunk", "electric", "vibrant", "glowing", "fluorescent"],
        "vintage": ["vintage", "retro", "nostalgic", "classic", "old", "aged", "film grain"],
        "documentary": ["documentary", "authentic", "raw", "unscripted", "real life", "behind the scenes"],
        "animated": ["animated", "animation", "cartoon", "illustrated", "drawn", "stylized"],
        "epic": ["epic", "grand", "heroic", "mythic", "legendary", "sweeping", "cinematic scope", "lord of the rings", "lotr", "fantasy"]
    }

    FORMAT_KEYWORDS = {
        "product_showcase": ["product", "showcase", "demo", "reveal", "feature", "unboxing"],
        "brand_manifesto": ["manifesto", "values", "mission", "belief", "philosophy", "vision", "movement"],
        "emotional_story": ["story", "journey", "narrative", "character", "human", "emotional"],
        "teaser": ["teaser", "tease", "preview", "coming soon", "announcement", "sneak peek"],
        "explainer": ["explain", "how to", "tutorial", "guide", "education", "teach", "learn"],
        "testimonial": ["testimonial", "review", "customer", "feedback", "experience", "story"],
        "lifestyle": ["lifestyle", "aspiration", "dream", "ideal", "living", "experience"]
    }

    TONE_KEYWORDS = {
        "mysterious": ["mystery", "mysterious", "enigma", "unknown", "secret", "hidden"],
        "triumphant": ["triumph", "victory", "win", "success", "achieve", "conquer"],
        "intimate": ["intimate", "personal", "close", "private", "tender", "gentle"],
        "energetic": ["energy", "dynamic", "exciting", "vibrant", "powerful", "intense"],
        "playful": ["playful", "fun", "whimsical", "lighthearted", "humorous", "silly"],
        "serious": ["serious", "professional", "corporate", "business", "formal"],
        "dramatic": ["dramatic", "intense", "powerful", "emotional", "gripping"],
        "serene": ["calm", "peaceful", "serene", "tranquil", "zen", "meditative"]
    }

    PACING_KEYWORDS = {
        "fast": ["fast", "quick", "rapid", "energetic", "dynamic", "action"],
        "slow": ["slow", "gradual", "calm", "peaceful", "meditative", "patient"],
        "mixed": ["varied", "dynamic", "contrast", "build", "progression"]
    }

    def __init__(self):
        """Initialize style detector"""
        pass

    def detect_style(
        self,
        user_input: str,
        constraints: Optional[Dict] = None,
        research_brief: Optional[Dict] = None
    ) -> Dict:
        """
        Detect creative style from user input and context.

        Args:
            user_input: User's creative brief/request
            constraints: Optional constraints dict (duration, mood, etc.)
            research_brief: Optional research results (industry, tone, etc.)

        Returns:
            Style profile dict with detected categories and confidence
        """
        # Combine all text for analysis
        analysis_text = user_input.lower()

        if constraints:
            analysis_text += " " + str(constraints).lower()

        if research_brief:
            analysis_text += " " + str(research_brief).lower()

        # Detect each style dimension
        aesthetic, aesthetic_conf = self._detect_aesthetic(analysis_text)
        format_type, format_conf = self._detect_format(analysis_text)
        tone, tone_conf = self._detect_tone(analysis_text)
        pacing, pacing_conf = self._detect_pacing(analysis_text)

        # Calculate overall confidence
        overall_confidence = (aesthetic_conf + format_conf + tone_conf + pacing_conf) / 4

        return {
            "aesthetic": aesthetic,
            "format": format_type,
            "tone": tone,
            "pacing": pacing,
            "confidence": overall_confidence,
            "confidence_breakdown": {
                "aesthetic": aesthetic_conf,
                "format": format_conf,
                "tone": tone_conf,
                "pacing": pacing_conf
            }
        }

    def _detect_aesthetic(self, text: str) -> Tuple[str, float]:
        """Detect visual aesthetic style"""
        scores = {}

        for aesthetic, keywords in self.AESTHETIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[aesthetic] = score

        if not scores:
            return "photorealistic", 0.3  # Default with low confidence

        # Get top aesthetic
        top_aesthetic = max(scores, key=scores.get)
        max_score = scores[top_aesthetic]

        # Calculate confidence (0-1 scale)
        confidence = min(1.0, max_score / 3.0)  # 3+ matches = high confidence

        return top_aesthetic, confidence

    def _detect_format(self, text: str) -> Tuple[str, float]:
        """Detect commercial format type"""
        scores = {}

        for format_type, keywords in self.FORMAT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[format_type] = score

        if not scores:
            return "emotional_story", 0.3  # Default

        top_format = max(scores, key=scores.get)
        confidence = min(1.0, scores[top_format] / 2.0)

        return top_format, confidence

    def _detect_tone(self, text: str) -> Tuple[str, float]:
        """Detect emotional/narrative tone"""
        scores = {}

        for tone, keywords in self.TONE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[tone] = score

        if not scores:
            return "dramatic", 0.3  # Default

        top_tone = max(scores, key=scores.get)
        confidence = min(1.0, scores[top_tone] / 2.0)

        return top_tone, confidence

    def _detect_pacing(self, text: str) -> Tuple[str, float]:
        """Detect pacing preference"""
        scores = {}

        for pacing, keywords in self.PACING_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[pacing] = score

        if not scores:
            return "mixed", 0.3  # Default

        top_pacing = max(scores, key=scores.get)
        confidence = min(1.0, scores[top_pacing] / 2.0)

        return top_pacing, confidence

    def get_style_profile_summary(self, style_profile: Dict) -> str:
        """Generate human-readable summary of detected style"""
        return f"""Style Profile Detected (Confidence: {style_profile['confidence']:.0%}):
- Aesthetic: {style_profile['aesthetic']} ({style_profile['confidence_breakdown']['aesthetic']:.0%})
- Format: {style_profile['format']} ({style_profile['confidence_breakdown']['format']:.0%})
- Tone: {style_profile['tone']} ({style_profile['confidence_breakdown']['tone']:.0%})
- Pacing: {style_profile['pacing']} ({style_profile['confidence_breakdown']['pacing']:.0%})"""
