import json
import urllib.request
import urllib.parse
import time
import os
import math

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Requires the user to export GOOGLE_PLACES_API_KEY
API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def search_google_places_nearby(lat, lon, radius=200.0):
    if not API_KEY:
        return []
        
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.primaryType,places.location,places.addressComponents,places.formattedAddress,places.googleMapsUri",
        "Content-Type": "application/json"
    }
    api_data = {
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon
                },
                "radius": float(radius)
            }
        }
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(api_data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            resp_data = json.loads(response.read().decode('utf-8'))
            places = resp_data.get('places', [])
            
            candidates = []
            for p in places[:10]: # Look at up to 10 nearest candidates
                r_lat = p.get('location', {}).get('latitude', 0)
                r_lon = p.get('location', {}).get('longitude', 0)
                if r_lat == 0 and r_lon == 0: continue
                
                name = p.get('displayName', {}).get('text', 'Unknown')
                cat = p.get('primaryType', 'misc').replace('_', ' ')
                maps_uri = p.get('googleMapsUri', '')
                address = p.get('formattedAddress', '')
                
                # Extract City and Country from addressComponents
                city = 'Unknown'
                country = 'Unknown'
                components = p.get('addressComponents', [])
                for comp in components:
                    types = comp.get('types', [])
                    if 'locality' in types or 'postal_town' in types or 'administrative_area_level_3' in types:
                        city = comp.get('longText', city)
                    if 'country' in types:
                        country = comp.get('longText', country)
                
                dist = haversine(lat, lon, r_lat, r_lon)
                
                candidates.append({
                    'name': name,
                    'category': cat,
                    'lat': r_lat,
                    'lon': r_lon,
                    'address': address,
                    'city': city,
                    'country': country,
                    'maps_uri': maps_uri,
                    'distance': round(dist, 1)
                })
            
            # Sort by distance
            candidates.sort(key=lambda x: x['distance'])
            return candidates
    except Exception as e:
        print(f"Error querying Google Places API (New): {e}")
        return []

def main():
    if not API_KEY:
        print("ERROR: Please set the GOOGLE_PLACES_API_KEY environment variable.")
        print("Example: set GOOGLE_PLACES_API_KEY=your_key && python correlate_nearby.py")
        return
        
    print("Loading perfect_clients.json...")
    try:
        with open('perfect_clients.json', 'r') as f:
            data = json.load(f)
            clients = data.get('clients', [])
    except Exception as e:
        print(f"Error reading perfect_clients.json: {e}")
        return

    print(f"Loaded {len(clients)} clients. Starting Google Places correlation for candidates around their precise locations...")

    for i, client in enumerate(clients):
        print(f"Processing client {i+1}/{len(clients)} at ({client['lat']}, {client['lon']})...")
        candidates = search_google_places_nearby(client['lat'], client['lon'])
        
        unique_candidates = []
        seen_names = set()
        
        # First candidate is inherently the original matched location Place. Let's make sure it's an option.
        original_primary = {
            'name': client.get('name', 'Unknown'),
            'category': client.get('category', 'misc'),
            'lat': client.get('lat'),
            'lon': client.get('lon'),
            'city': client.get('city', 'Unknown'),
            'country': client.get('country', 'Unknown'),
            'maps_uri': client.get('maps_uri', ''),
            'distance': 0.0
        }
        
        unique_candidates.append(original_primary)
        seen_names.add(original_primary['name'])
        
        for c in candidates:
            if c['name'] not in seen_names:
                seen_names.add(c['name'])
                unique_candidates.append(c)
                
        client['candidates'] = unique_candidates
        
        time.sleep(0.05) # Rate limiting
            
    print("Saving to correlated_nearby.json...")
    with open('correlated_nearby.json', 'w') as f:
        json.dump({'clients': clients}, f, indent=2)
        
    print("Done! Extracted candidates for every client.")

if __name__ == "__main__":
    main()
