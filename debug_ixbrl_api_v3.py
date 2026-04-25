"""
Test different TenthNoteAppCode values.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ixbrl_key = os.getenv("IXBRL_API_KEY")

print("🔍 Testing TenthNoteAppCode values")
print("=" * 50)

# Try different app code values
app_codes = [
    "convert-ixbrl",
    "ConvertIXBRL",
    "convert_ixbrl",
    "ixbrl",
    "sophiepenrose@virginmedia.com",  # Account ID
    ""  # Empty
]

url = "https://convert-ixbrl.co.uk/api/financialsMetaData"
params = {
    "companyNumber": "13638252",
    "apiVersion": "2"
}

for app_code in app_codes:
    print(f"\nTrying TenthNoteAppCode: '{app_code}'")
    headers = {
        "X-API-Secret": ixbrl_key,
        "TenthNoteAppCode": app_code,
        "User-Agent": "CompanyInsightApp/1.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ SUCCESS! Keys: {list(data.keys())}")
                print(f"  Sample data: {str(data)[:200]}")
                break
            except:
                print(f"  Response: {response.text[:100]}")
        else:
            print(f"  Error: {response.text[:80]}")
            
    except Exception as e:
        print(f"  Exception: {str(e)[:80]}")
