# Network Shape Client Maps Analysis

This project is a high-accuracy, automated pipeline designed to extract business locations from embedded Google My Maps datasets (KML/HTML) and flawlessly resolve their exact digital identities using the Google Places API.

The project features a sleek dark-mode, animated frontend dashboard using Leaflet.js and a comprehensive CSV export pipeline capable of mapping hundreds of businesses.

## Features

- **Raw My Maps Data Extraction**: Deep parses embedded `_pageData` Javascript payloads directly from raw Google My Maps HTML source code. This bypasses fuzzy geographical coordinate matching by extracting Google's internal `Place IDs` explicitly.
- **Perfect Accuracy Correlation (`correlate_perfect.py`)**: Uses the new Google Places API (v1) to query exact `Place IDs`. It aggregates perfect 1-to-1 matches containing business names, deep address components (city, country), primary categories, and direct `googleMapsUri` links.
- **Sleek Web Dashboard (`index.html`, `app.js`)**: An animated, high-performance dark-themed UI to visualize the final dataset, search through clients, and jump straight to their maps properties.
- **Structured Export (`export_csv.py`)**: Automatically converts the resulting JSON payloads into a rich, analyst-ready `network_shape_clients.csv` document.

## Setup

1. **Install Dependencies**
   No heavy external libraries are needed for the scripts outside of a standard Python 3.x environment. The dashboard uses CDN links for UI dependencies.
   
2. **Environment Configuration**
   You must acquire a Google Cloud Platform API Key with the **Places API (New)** enabled.
   
   Configure this in your local environment:
   ```bash
   # Windows PowerShell
   $env:GOOGLE_PLACES_API_KEY="YOUR_API_KEY_HERE"
   
   # Linux/macOS
   export GOOGLE_PLACES_API_KEY="YOUR_API_KEY_HERE"
   ```

## Usage

1. **Extract Raw IDs**
   Given `map2.html` and `map3.html` (the source code from a Google My Maps embed), run:
   ```bash
   python extract_raw.py
   ```
   *This outputs `extracted_raw.json` with 200+ raw Place IDs and encoded Protobufs.*

2. **Fetch Exact Business Listings**
   ```bash
   python correlate_perfect.py
   ```
   *This queries the Places API iteratively and outputs the final master document: `perfect_clients.json`.*

3. **Generate CSV Report**
   ```bash
   python export_csv.py
   ```
   *This converts `perfect_clients.json` into a readable spreadsheet `network_shape_clients.csv`.*

4. **Launch the Dashboard**
   ```bash
   python -m http.server 8000
   ```
   *Navigate to `http://localhost:8000` to interact with the map interface.*
