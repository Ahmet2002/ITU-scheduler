import requests
import browser_cookie3

def get_cookies_and_auth_key():
    try:
        cookies = browser_cookie3.chrome(domain_name='obs.itu.edu.tr')
        
        if not any([cookie.name == "LoginCookie" for cookie in cookies]):
            return "", ""

        jwt_url = "https://obs.itu.edu.tr/ogrenci/auth/jwt"

        headers = {
            "authorization": "Bearer",
            "accept": "application/json, text/plain, */*"
        }

        response = requests.get(jwt_url, headers=headers, cookies=cookies)

    except:
        return "", ""

    auth_key = ""
    if response.status_code == 200:
        auth_key = response.text.strip()
        # print("Retrieved JWT token:", auth_key)
    else:
        print("Failed to retrieve token:", response.status_code)

    return auth_key, cookies