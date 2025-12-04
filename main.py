import argparse
import sys
import os

# Add the current directory to sys.path so we can import ott_ad_builder
sys.path.append(os.getcwd())

from ott_ad_builder.pipeline import AdGenerator

def main():
    parser = argparse.ArgumentParser(description="OTT Ad Builder CLI")
    parser.add_argument("input", nargs="?", help="Product description or URL")
    parser.add_argument("--plan", action="store_true", help="Generate plan only")
    parser.add_argument("--resume", action="store_true", help="Resume from plan.json")
    
    args = parser.parse_args()
    
    generator = AdGenerator()
    
    if args.resume:
        generator.resume()
    elif args.input:
        generator.plan(args.input)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
