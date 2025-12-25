from flask import Flask, request, jsonify
import requests
import csv
import time

app = Flask(__name__)

# Load taxonomy mapping from CSV
def load_taxonomy_mapping():
    """Load tag to taxonomy ID mapping from CSV file."""
    mapping = {}
    with open('taxonomy_mapping.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Keep original case for matching
            mapping[row['tag']] = row['taxonomy_id']
    return mapping

TAXONOMY_MAPPING = load_taxonomy_mapping()

def fetch_roblox_items(taxonomy_id, target_count=500):
    """
    Fetch item IDs from Roblox catalog API.
    
    Args:
        taxonomy_id: The taxonomy ID for the category
        target_count: Number of IDs to collect (default 500)
    
    Returns:
        List of item IDs (first 500 results)
    """
    base_url = "https://catalog.roblox.com/v2/search/items/details"
    params = {
        'taxonomy': taxonomy_id,
        'minPrice': 15,
        'salesTypeFilter': 1,
        'sortType': 2,
        'sortAggregation': 1,
        'limit': 120
    }
    
    all_ids = []
    cursor = None
    
    while len(all_ids) < target_count:
        # Add cursor if we have one from previous request
        if cursor:
            params['cursor'] = cursor
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract IDs from the data
            if 'data' in data:
                for item in data['data']:
                    if 'id' in item:
                        all_ids.append(item['id'])
                        if len(all_ids) >= target_count:
                            break
            
            # Check if we have enough IDs or no more pages
            if len(all_ids) >= target_count:
                break
            
            # Get next page cursor
            next_cursor = data.get('nextPageCursor')
            if not next_cursor:
                # No more pages available
                break
            
            cursor = next_cursor
            
            # Wait 1 second before next request
            time.sleep(1)
            
        except requests.exceptions.Timeout:
            print(f"Request timeout, collected {len(all_ids)} IDs so far")
            break
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            break
    
    # Return only the first 500 IDs
    return all_ids[:target_count]

@app.route('/scrape', methods=['POST'])
def scrape_items():
    """
    API endpoint to scrape Roblox catalog items by tag.
    
    Expected payload:
    {
        "tag": "head"  // or "shirt", "pants", etc.
    }
    
    Returns:
    {
        "ids": [123456, 789012, ...],  // Array of first 500 item IDs
        "count": 500,
        "tag": "head"
    }
    """
    try:
        # Get tag from request payload
        data = request.get_json()
        
        if not data or 'tag' not in data:
            return jsonify({
                'error': 'Missing "tag" in request payload'
            }), 400
        
        tag = data['tag']
        
        # Look up taxonomy ID
        if tag not in TAXONOMY_MAPPING:
            return jsonify({
                'error': f'Unknown tag: {tag}',
                'available_tags': list(TAXONOMY_MAPPING.keys())
            }), 400
        
        taxonomy_id = TAXONOMY_MAPPING[tag]
        
        # Fetch IDs
        ids = fetch_roblox_items(taxonomy_id)
        
        return jsonify({
            'ids': ids,
            'count': len(ids),
            'tag': tag
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
