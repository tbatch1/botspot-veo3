"""
Optimization Test Runner
Runs all optimization tests and provides detailed output
"""

import pytest
import sys
import os
from pathlib import Path

def main():
    """Run all optimization tests"""

    print("="*80)
    print("OTT AD BUILDER - WORKFLOW OPTIMIZATION TEST SUITE")
    print("="*80)
    print()

    # Run pytest with verbose output
    test_file = Path("tests/test_optimizations.py")

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1

    print(f"Running tests from: {test_file}")
    print()

    # Run tests with pytest
    args = [
        str(test_file),
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "--color=yes",  # Colored output
        "-W", "ignore::DeprecationWarning",  # Ignore deprecation warnings
    ]

    exit_code = pytest.main(args)

    print()
    print("="*80)

    if exit_code == 0:
        print("[SUCCESS] ALL TESTS PASSED!")
        print()
        print("Optimizations validated:")
        print("  [PASS] Phase 1: Research caching, smart extraction, Opus tokens, AI slop removal")
        print("  [PASS] Phase 2: Parallel image generation, parallel audio, character consistency")
        print("  [PASS] Phase 3: Parallel video, fallback chains, adaptive encoding")
    else:
        print(f"[FAIL] TESTS FAILED (exit code: {exit_code})")
        print()
        print("Some optimizations may need fixes. Check output above.")

    print("="*80)

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
