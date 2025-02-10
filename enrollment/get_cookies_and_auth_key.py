import requests
import rookiepy

def get_cookies_and_auth_key():
    try:
        cookies = rookiepy.chrome(['obs.itu.edu.tr'])

        good_to_go = False
        for cookie in cookies:
            if cookie['name'] == "LoginCookie":
                good_to_go = True
        
        if not good_to_go:
            return "", ""

        jwt_url = "https://obs.itu.edu.tr/ogrenci/auth/jwt"

        headers = {
            "authorization": "Bearer",
            "accept": "application/json, text/plain, /"
        }

        cookies = {cookie['name']: cookie['value'] for cookie in cookies}
        response = requests.get(jwt_url, headers=headers, cookies=cookies)

    except Exception as e:
        print(e)
        return "", ""

    auth_key = ""
    if response.status_code == 200:
        auth_key = response.text.strip().strip('"')
        # print("Retrieved JWT token:", auth_key)
    else:
        print("Failed to retrieve token:", response.status_code)

    return auth_key, cookies