"""
Try basic auth and other combinations.
"""

import os
import requests
from dotenv import load_dotenv
import base64

load_dotenv()

ixbrl_key = os.getenv("IXBRL_API_KEY")
email = "sophiepenrose@virginmedia.com"

print("🔍 Testing alternative authentication methods")
print("=" * 50)

url = "https://convert-ixbrl.co.uk/api/financialsMetaData"
params = {
    "companyNumber": "13638252",
    "apiVersion": "2"
}

methods = [
    {
        "name": "Basic Auth (email:key)",
        "headers": {
            "Authorization": "Basic " + base64.b64encode(f"{email}:{ixbrl_key}".encode()).decode(),
            "User-Agent": "CompanyInsightApp/1.0"
        }
    },
    {
        "name": "Basic Auth (email only)",
        "headers": {
            "Authorization": "Basic " + base64.b64encode(f"{email}".encode()).decode(),
            "User-Agent": "CompanyInsightApp/1.0"
        }
    },
    {
        "name": "Email as TenthNoteAppCode",
        "headers": {
            "X-API-Secret": ixbrl_key,
            "TenthNoteAppCode": email,
            "User-Agent": "CompanyInsightApp/1.0"
        }
    },
    {
        "name": "Just X-API-Secret",
        "headers": {
            "X-API-Secret": ixbrl_key,
            "User-Agent": "CompanyInsightApp/1.0"
        }
    }
]

for method in methods:
    print(f"\nTrying: {method['name']}")
    try:
        response = requests.get(url, params=params, headers=method['headers'], timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ SUCCESS!")
                print(f"  Response keys: {list(data.keys())}")
                if 'turnover' in data:
                    print(f"  Turnover: £{data['turnover']:,.0f}")
                break
            except Exception as e:
                print(f"  Parse error: {e}")
        else:
            print(f"  Error: {response.text[:120]}")
            
    except Exception as e:
        print(f"  Exception: {str(e)[:80]}")
