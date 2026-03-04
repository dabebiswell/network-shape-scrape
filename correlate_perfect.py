import urllib.request
import json
import os
import time

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")

def fetch_place_details(place_id):
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "displayName,primaryType,location,formattedAddress,addressComponents,types,googleMapsUri"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read())
    except Exception as e:
        print(f"Error fetching {place_id}: {e}")
        return None

def process_places():
    if not API_KEY:
        print("Missing GOOGLE_PLACES_API_KEY environment variable. Cannot query Places API.")
        return

    with open('extracted_raw.json', 'r') as f:
        data = json.load(f)
        places = data.get('places', [])
    
    print(f"Loaded {len(places)} raw place IDs. Starting exact lookup.")
    
    results = []
    
    for i, place in enumerate(places):
        place_id = place.get('place_id')
        lat = place.get('lat')
        lon = place.get('lon')
        
        print(f"Processing ({i+1}/{len(places)}) {place_id}...")
        
        details = fetch_place_details(place_id)
        if details:
            name = details.get('displayName', {}).get('text', 'Unknown')
            cat = details.get('primaryType', 'misc').replace('_', ' ')
            address = details.get('formattedAddress', '')
            maps_uri = details.get('googleMapsUri', '')
            
            city = 'Unknown'
            country = 'Unknown'
            components = details.get('addressComponents', [])
            for comp in components:
                types = comp.get('types', [])
                if 'locality' in types or 'postal_town' in types or 'administrative_area_level_3' in types:
                    city = comp.get('longText', city)
                if 'country' in types:
                    country = comp.get('longText', country)
            
            results.append({
                'lat': lat,
                'lon': lon,
                'name': name,
                'category': cat,
                'address': address,
                'city': city,
                'country': country,
                'maps_uri': maps_uri,
                'place_id': place_id
            })
        else:
            # Fallback if Place API fails on this ID
            results.append({
                'lat': lat,
                'lon': lon,
                'name': 'Unknown',
                'category': '',
                'address': '',
                'city': '',
                'country': '',
                'maps_uri': '',
                'place_id': place_id
            })
        
        time.sleep(0.05) # Rate limiting
        
    with open('perfect_clients.json', 'w') as f:
        json.dump({'clients': results}, f, indent=2)
        
    print("Done! Saved accurately matched properties to perfect_clients.json")

if __name__ == '__main__':
    process_places()
