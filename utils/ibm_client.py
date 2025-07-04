import os
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

IBM_API_KEY = os.getenv("IBM_API_KEY")
IBM_SERVICE_URL = os.getenv("IBM_SERVICE_URL")

# Debug print to ensure loaded
print("IBM_API_KEY loaded:", bool(IBM_API_KEY))
print("IBM_SERVICE_URL loaded:", bool(IBM_SERVICE_URL))

if not IBM_API_KEY or not IBM_SERVICE_URL:
    raise ValueError("❌ IBM_API_KEY or IBM_SERVICE_URL not set in your .env file!")

# Setup authenticator
authenticator = IAMAuthenticator(IBM_API_KEY)

# Create NLU client
nlu = NaturalLanguageUnderstandingV1(
    version='2022-04-07',
    authenticator=authenticator
)

nlu.set_service_url(IBM_SERVICE_URL)
