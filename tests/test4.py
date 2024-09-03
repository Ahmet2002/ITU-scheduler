import requests
from bs4 import BeautifulSoup

url = 'https://www.sis.itu.edu.tr/TR/ogrenci/lisans/onsartlar/onsartlar.php'

selected_major_code = 'EHB'

# Step 3: Send a POST request with the form data
form_data = {
    'derskodu': selected_major_code,
    # Add any other necessary form fields here
}

# Send the POST request
response = requests.post(url, data=form_data)

# Check the response
if response.status_code == 200:
    print("Form submitted successfully!")
else:
    print(f"Failed to submit the form. Status code: {response.status_code}")

print(response.text)
