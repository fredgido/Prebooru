import time
import requests

def DanbooruRequest(url, params):
    for i in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Pausing for network timeout...")
            time.sleep(5)
            continue
        break
    else:
        return {'error': True, 'message': "Connection errors exceeded."}
    if response.status_code == 200:
        return {'error': False, 'json': response.json()}
    else:
        return {'error': True, 'message': "HTTP %d: %s" % (response.status_code, response.reason)}

def GetArtistsByUrl(url):
    request_url = 'https://danbooru.donmai.us/artist_urls.json'
    params = {
        'search[url]': url,
        'only': 'url,artist'
    }
    data = DanbooruRequest(request_url, params)
    if data['error']:
        return data
    artists = [artist_url['artist'] for artist_url in data['json']]
    return {'error': False, 'artists': artists}
