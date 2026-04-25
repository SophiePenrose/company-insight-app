"""
Debug iXBRL API with different authentication methods.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ixbrl_key = os.getenv("IXBRL_API_KEY")

print("🔍 Testing different iXBRL API authentication methods")
print("=" * 50)

# Try different header combinations
auth_methods = [
    {
        "name": "X-API-Secret",
        "headers": {"X-API-Secret": ixbrl_key}
    },
    {
        "name": "API-Secret", 
        "headers": {"API-Secret": ixbrl_key}
    },
    {
        "name": "Authorization Bearer",
        "headers": {"Authorization": f"Bearer {ixbrl_key}"}
    },
    {
        "name": "X-API-Key + TenthNote",
        "headers": {"X-API-Key": ixbrl_key, "TenthNoteAppCode": "convert-ixbrl"}
    }
]

url = "https://convert-ixbrl.co.uk/api/financialsMetaData"
params = {
    "companyNumber": "13638252",
    "apiVersion": "2"
}

for method in auth_methods:
    print(f"\nTrying: {method['name']}")
    headers = method['headers'].copy()
    headers["User-Agent"] = "CompanyInsightApp/1.0"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ SUCCESS! Keys: {list(data.keys())[:5]}")
                break
            except:
                print(f"  Response: {response.text[:100]}")
        elif response.status_code == 400:
            print(f"  Error: {response.text}")
        else:
            print(f"  Response: {response.text[:100]}")
            
    except Exception as e:
        print(f"  Exception: {str(e)[:100]}")
