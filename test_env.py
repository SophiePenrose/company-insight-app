from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv("COMPANIES_HOUSE_API_KEY"))
