import requests

def WorkerCheckUploads():
    try:
        requests.get('http://127.0.0.1:4000/check_uploads', timeout=2)
    except Exception as e:
        print("Unable to contact worker:", e)
