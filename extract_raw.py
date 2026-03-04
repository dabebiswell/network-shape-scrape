import re
import json
import base64

def extract_from_html(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the _pageData payload
    match = re.search(r'var _pageData = "(.*?)";</script>', content)
    if not match:
        print(f"Could not find _pageData in {filename}")
        return []

    # The payload is json encoded as a string, but it has some strange escaped quotes sometimes
    raw_data = match.group(1)
    # The string is a literal javascript string. Let's unescape it.
    raw_data = raw_data.encode().decode('unicode_escape')
    
    try:
        data = json.loads(raw_data)
    except Exception as e:
        print(f"JSON parse error on {filename}: {e}")
        return []

    places = []

    # _pageData[1][6][0][12][0][13][0] usually houses the array of placemarks
    # We will just recursively search the entire JSON structure for arrays that look like placemarks
    
    def find_places(node):
        if isinstance(node, list):
            # A typical placemark node might look like:
            # ["529DD660BE523C19", [[[49.25,-122.76]]], null, null, 0, [["name", ["NSH"], 1], ... , [null, "ChIJDZql6AfWhVQR2IfAMxoqznc", true]], ...]
            # We can look for lists that start with a hex ID, or just search for the place IDs directly.
            
            # Simple heuristic: Look for ["name", ["some_string"]] and a place ID nearby
            if len(node) > 5 and isinstance(node[0], str) and isinstance(node[1], list):
                # check if there's coordinates
                coords = None
                try:
                    coords = node[1][0][0]
                    if len(coords) == 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
                        # Found coords
                        pass
                except:
                    pass
                
                if coords:
                    place_id = None
                    # try to find string starting with 'ChIJ' or 'Ei'
                    for item in node:
                        if isinstance(item, list):
                            for sub in item:
                                if isinstance(sub, list):
                                    for leaf in sub:
                                        if isinstance(leaf, str) and (leaf.startswith('ChIJ') or leaf.startswith('Ei')):
                                            place_id = leaf
                                            break
                            if place_id:
                                break
                    
                    if place_id:
                        places.append({
                            'lat': coords[0],
                            'lon': coords[1],
                            'place_id': place_id
                        })
            
            for item in node:
                find_places(item)

    find_places(data)
    return places

all_places = extract_from_html('map2.html') + extract_from_html('map3.html')

print(f"Extracted {len(all_places)} places.")

with open('extracted_raw.json', 'w') as f:
    json.dump({'places': all_places}, f, indent=2)
