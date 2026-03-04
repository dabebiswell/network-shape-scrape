import json
import csv

def generate_csv():
    try:
        with open('correlated_nearby.json', 'r') as f:
            data = json.load(f)
            clients = data.get('clients', [])
    except Exception as e:
        print(f"Error reading correlated_nearby.json: {e}")
        return

    csv_filename = "network_shape_clients.csv"
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Location Lat', 'Location Lon', 'Status', 'Business Name', 'Category', 'Confidence (Distance)', 'City', 'Country', 'Google Maps Link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        generic_categories = {'premise', 'street address', 'route', 'intersection', 'subpremise', 'neighborhood'}
        
        for client in clients:
            candidates = client.get('candidates', [])
            has_candidates = len(candidates) > 0
            
            default_index = 0
            if has_candidates:
                for idx, cand in enumerate(candidates):
                    cat = cand.get('category', '').lower()
                    name = cand.get('name', '')
                    if cat not in generic_categories and name != 'Unknown':
                        default_index = idx
                        break
            
            primary = candidates[default_index] if has_candidates else client
            is_unknown = primary.get('name') == 'Unknown' or not primary.get('name')
            
            status = "Pending" if is_unknown else "Identified"
            business_name = 'Unknown Business' if is_unknown else primary.get('name', '')
            
            dist = primary.get('distance', 0.0)
            if dist == 0.0:
                confidence_str = "Exact Match (100%)"
            else:
                confidence_str = f"Nearest Business ({dist}m)"
            
            writer.writerow({
                'Location Lat': client.get('lat'),
                'Location Lon': client.get('lon'),
                'Status': status,
                'Business Name': business_name,
                'Category': primary.get('category', client.get('category', '')),
                'Confidence (Distance)': confidence_str,
                'City': primary.get('city', client.get('city', '')),
                'Country': primary.get('country', client.get('country', '')),
                'Google Maps Link': primary.get('maps_uri', client.get('maps_uri', ''))
            })
                
    print(f"Successfully exported {len(clients)} records to {csv_filename}")

if __name__ == '__main__':
    generate_csv()
