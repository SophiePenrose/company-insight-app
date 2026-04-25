"""
Debug iXBRL API responses to see what's being returned.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ixbrl_key = os.getenv("IXBRL_API_KEY")

print("🔍 Testing iXBRL API directly")
print("=" * 50)
print(f"API Key: {ixbrl_key[:10]}...")
print()

# Test the direct API call
url = "https://convert-ixbrl.co.uk/api/financialsMetaData"
params = {
    "companyNumber": "13638252",
    "apiVersion": "2"
}
headers = {
    "X-API-Key": ixbrl_key,
    "User-Agent": "CompanyInsightApp/1.0"
}

print(f"Testing URL: {url}")
print(f"Params: {params}")
print(f"Headers: X-API-Key: {ixbrl_key[:10]}...\n")

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}\n")
    print(f"Response Body:\n{response.text}\n")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Parsed JSON Keys: {list(data.keys())}")
        except:
            print("Could not parse as JSON")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
