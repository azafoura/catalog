from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
import requests
import csv
import time
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

# ── In-memory cache (24-hour TTL) ──────────────────────────────────
# Key: (tag, limit)  →  Value: {"timestamp": float, "response": dict}
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours
_cache: dict = {}

# Authentication credentials (use environment variables in production)
API_USERNAME = os.getenv('API_USERNAME', 'arthur')
API_PASSWORD = os.getenv('API_PASSWORD', 'arthur')

@auth.verify_password
def verify_password(username, password):
    """Verify username and password."""
    if username == API_USERNAME and password == API_PASSWORD:
        return username
    return None

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
        dict with keys:
            ids          – list of item IDs (up to target_count)
            reached_end  – True when there are no more pages to fetch
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
    reached_end = False

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

            # Get next page cursor
            next_cursor = data.get('nextPageCursor')
            if not next_cursor:
                # No more pages available – we've reached the end
                reached_end = True
                break

            # Check if we have enough IDs
            if len(all_ids) >= target_count:
                break

            cursor = next_cursor

            # Wait 1 second before next request to avoid rate-limiting
            time.sleep(1)

        except requests.exceptions.Timeout:
            print(f"Request timeout, collected {len(all_ids)} IDs so far")
            break
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            break

    return {
        'ids': all_ids[:target_count],
        'reached_end': reached_end,
    }

@app.route('/scrape', methods=['POST'])
@auth.login_required
def scrape_items():
    """
    API endpoint to scrape Roblox catalog items by tag.

    Expected JSON payload:
    {
        "tag":   "head",   // required – or "shirt", "pants", etc.
        "limit": 500        // optional – number of asset IDs to fetch (default 500)
    }

    Returns:
    {
        "ids":         [123456, 789012, ...],
        "count":       500,
        "tag":         "head",
        "limit":       500,
        "reached_end": false,   // true when every available item has been collected
        "cached":      false    // true when the response was served from cache
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
        limit = int(data.get('limit', 500))

        if limit < 1:
            return jsonify({'error': '"limit" must be a positive integer'}), 400

        # Look up taxonomy ID
        if tag not in TAXONOMY_MAPPING:
            return jsonify({
                'error': f'Unknown tag: {tag}',
                'available_tags': list(TAXONOMY_MAPPING.keys())
            }), 400

        taxonomy_id = TAXONOMY_MAPPING[tag]

        # ── Check cache ────────────────────────────────────────────
        cache_key = (tag, limit)
        cached_entry = _cache.get(cache_key)
        if cached_entry and (time.time() - cached_entry['timestamp']) < CACHE_TTL_SECONDS:
            resp = cached_entry['response'].copy()
            resp['cached'] = True
            return jsonify(resp), 200

        # ── Fetch from Roblox ──────────────────────────────────────
        result = fetch_roblox_items(taxonomy_id, target_count=limit)

        response_body = {
            'ids': result['ids'],
            'count': len(result['ids']),
            'tag': tag,
            'limit': limit,
            'reached_end': result['reached_end'],
            'cached': False,
        }

        # Store in cache
        _cache[cache_key] = {
            'timestamp': time.time(),
            'response': response_body,
        }

        return jsonify(response_body), 200

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
