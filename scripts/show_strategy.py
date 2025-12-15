import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ott_ad_builder.providers.strategist import StrategistProvider
from ott_ad_builder.providers.researcher import ResearcherProvider

def show_botspot_strategy():
    print("🕵️  Re-running Strategist Analysis for Botspot.trade...")
    
    # 1. Research
    researcher = ResearcherProvider()
    url = "https://botspot.trade"
    brief = researcher.fetch_and_analyze(url)
    print(f"\n📄 RESEARCH BRIEF:\n{brief[:500]}...\n[...snipped...]")

    # 2. Strategy
    strategist = StrategistProvider()
    constraints = {
        "character_concept": "Tom from Botspot: A calm, helpful guy in a green polo who appears instantly when traders panic.",
        "image_provider": "flux"
    }
    
    strategy = strategist.develop_strategy(
        topic="Botspot.trade - AI Trading Agents",
        website_data=brief,
        constraints=constraints
    )

    print("\n🧠 STRATEGIST OUTPUT (CLAUDE OPUS 4.5):")
    print(json.dumps(strategy, indent=2))

if __name__ == "__main__":
    show_botspot_strategy()
