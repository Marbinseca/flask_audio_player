
import sys
import logging
from youtube_dl_helper import AudioExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extraction(url):
    print(f"Testing extraction for: {url}")
    extractor = AudioExtractor()
    info = extractor.extract_info(url)
    
    if 'error' in info:
        print(f"ERROR: {info['error']}")
        sys.exit(1)
    else:
        print(f"SUCCESS: Found {info.get('title')}")
        print(f"Platform: {info.get('platform')}")
        sys.exit(0)

if __name__ == "__main__":
    # Use a known safe video (e.g., a creative commons video or official music video)
    test_url = "https://www.youtube.com/watch?v=BaW_jenozKc" # generic video
    test_extraction(test_url)
