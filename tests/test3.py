import requests
from bs4 import BeautifulSoup

# URL of the page with the form
url = "https://www.sis.itu.edu.tr/TR/ogrenci/lisans/ders-bilgileri/ders-bilgileri.php"

# Values you want to submit (you can modify these values dynamically)
form_data = {
    'subj': 'EHB',   # Subject code (e.g., 'EHB')
    'numb': '110',   # Course number (e.g., '110')
}

# Perform the POST request
response = requests.post(url, data=form_data)

# Check if the request was successful
if response.status_code == 200:
    print("Form submitted successfully.")
    print(response.text)
    
#     # Parse the response content using BeautifulSoup
#     soup = BeautifulSoup(response.content, 'html.parser')
    
#     # Example: Extract some specific information from the response
#     # Here you would need to modify this part based on the actual HTML structure of the response
#     # For example, let's say prerequisites are in a div with id "prereq-info"
#     prereq_info = soup.find('div', id='prereq-info')
#     if prereq_info:
#         print("Prerequisite Information:")
#         print(prereq_info.text.strip())
#     else:
#         print("Prerequisite information not found.")
# else:
#     print(f"Failed to submit form. Status code: {response.status_code}")
