import requests

def send_request(auth_key, cookies, ECRNS, SCRNS=[]):
    enrollment_url = "https://obs.itu.edu.tr/api/ders-kayit/v21"
    payload = {
        "ECRN": ECRNS,
        "SCRN": SCRNS
    }

    # Note: Include the token in the Authorization header as "Bearer <token>"
    enrollment_headers = {
        "authorization": f"Bearer {auth_key}",
        "content-type": "application/json",
        "accept": "application/json, text/plain, */*"
    }

    ret = ""
    enrollment_response = requests.post(enrollment_url, json=payload, headers=enrollment_headers, cookies=cookies)

    try:
        if enrollment_response.status_code == 200:
            ret = enrollment_response.json()
            print("Enrollment response:", ret)
        else:
            print("Enrollment failed, status code:", enrollment_response.status_code)
    except:
        return ""
    
    return ret