import requests
from bs4 import BeautifulSoup
import json

# Start a session
session = requests.Session()

# Step 1: Get the initial page to extract the RequestVerificationToken
response = session.get("https://obs.itu.edu.tr/public/DersProgram")
soup = BeautifulSoup(response.content, "html.parser")

# Extract the verification token from the hidden input field
token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]


# Step 2: Prepare the form data to submit the form
form_data = {
    "ProgramSeviyeTipiAnahtari": "LS",  # Example: 'LS' for Lisans
    "dersBransKoduId": "196",  # Example: '289' for EEE (Electricity)
    "__RequestVerificationToken": token  # Include the token
}

# Step 3: Submit the form using a POST request
post_response = session.post("https://obs.itu.edu.tr/public/DersProgram/DersProgramSearch", data=form_data)


data = json.loads(post_response.text)
pretty_json = json.dumps(data, indent=4, ensure_ascii=False)
print(pretty_json)
