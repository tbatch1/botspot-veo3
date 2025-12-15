# Archived Providers

This directory contains video generation providers that are not currently in active use but may be restored in the future.

## Kling AI (kling.py)

**Archived Date:** December 11, 2025  
**Reason:** Not currently configured, reducing maintenance burden  
**Status:** Can be restored if needed

### To Restore Kling AI:

1. Move `archived/kling.py` back to `providers/kling.py`
2. Update `pipeline.py` to import and initialize KlingProvider
3. Update `parallel_utils.py` ParallelVideoGenerator to accept kling_provider
4. Set PIAPI_API_KEY in .env file
5. Update fallback chain to include Kling: Runway → Veo → Kling

### Original Configuration:

- **Model:** kling-v1.6
- **Gateway:** PiAPI (piapi.ai)
- **Cost:** $16/month subscription + 660 credits/month
- **Speed:** 60-180 seconds per 5-second video
- **Quality:** High (16:9 aspect ratio)

### Original Integration Points:

- `pipeline.py` line ~360: Provider initialization
- `pipeline.py` line ~385: Fallback chain
- `parallel_utils.py` line ~210: ParallelVideoGenerator class
- `config.py` line ~65: API key configuration
