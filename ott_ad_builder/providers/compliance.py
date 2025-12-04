from .gemini import GeminiProvider
from ..state import Script
import json

class ComplianceProvider:
    def __init__(self):
        self.llm = GeminiProvider()
        self.default_rules = [
            "No false or misleading claims.",
            "No medical advice or unverified health claims.",
            "Must be suitable for general audiences (PG-13).",
            "No copyright infringement of known brands (other than the target brand).",
            "Must include 'Terms and conditions apply' if mentioning discounts."
        ]

    def review(self, script: Script, industry: str = "General") -> Script:
        """
        Reviews the script for compliance violations and auto-corrects if necessary.
        """
        print(f"⚖️ Compliance Officer: Reviewing script for {industry} regulations...")
        
        rules_text = "\n- ".join(self.default_rules)
        
        prompt = f"""
        You are a strict Legal Compliance Officer for an ad agency.
        Review the following ad script against these Brand Safety Rules:
        
        RULES:
        - {rules_text}
        - Industry specific rules for: {industry}
        
        SCRIPT:
        {script.json()}
        
        INSTRUCTIONS:
        1. Identify any violations.
        2. If violations exist, REWRITE the problematic lines to be compliant while keeping the creative intent.
        3. If no violations, return the script exactly as is.
        4. Output ONLY the valid JSON of the (potentially corrected) Script object. Do not add markdown formatting.
        """
        
        try:
            response_text = self.llm.model.generate_content(prompt).text
            # Clean up potential markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(response_text)
            validated_script = Script(**data)
            
            if validated_script != script:
                print("⚠️ Compliance Issue Found: Script was auto-corrected.")
            else:
                print("✅ Compliance Check Passed.")
                
            return validated_script
            
        except Exception as e:
            print(f"❌ Compliance Check Failed: {e}")
            print("   Proceeding with original script (User should review manually).")
            return script
