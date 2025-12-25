# Roblox Catalog Scraper API

A Python Flask API that scrapes Roblox catalog items by tag and returns item IDs.

## Features

- Accepts requests with a tag in the payload (head, shirt, pants, etc.)
- Scrapes data from Roblox catalog API
- Handles pagination automatically using `nextPageCursor`
- Returns the first 500 item IDs
- Uses 1-second delay between paginated requests

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Start the server

```bash
python api.py
```

The server will run on `http://localhost:5000`

### Make a request

```bash
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"tag": "Hair"}'
```

Or with accessories:

```bash
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{"tag": "Face (Accessory)"}'
```

### Response format

```json
{
  "ids": [123456, 789012, ...],
  "count": 500,
  "tag": "Hair"
}
```

## Available Tags

Edit `taxonomy_mapping.csv` to add or modify tags and their corresponding taxonomy IDs.

### Clothing Items:
- Hair
- T-Shirts
- Shirts
- Sweaters
- Jackets
- Pants
- Shorts
- DressesSkirts
- Bodysuits
- Shoes
- Classic Shirts
- Classic T-Shirts
- Classic Pants

### Body Parts:
- Heads (Body)
- Classic Faces

### Accessories:
- Head (Accessory)
- Face (Accessory)
- Neck Accessory
- Shoulder Accessory
- Front Accessory
- Back Accessory
- Waist Accessory

### Other:
- Emotes

## How it works

1. API receives a POST request with a tag in the payload (e.g., "Hair", "Face (Accessory)")
2. Looks up the corresponding taxonomy ID from `taxonomy_mapping.csv`
3. Makes requests to Roblox catalog API with limit=120 (maximum allowed by Roblox)
4. If fewer than 500 results, uses `nextPageCursor` to fetch additional pages
5. Waits 1 second between paginated requests to avoid rate limiting
6. Returns the first 500 item IDs collected in order

**Note:** Tags are case-sensitive and must match exactly as listed in the CSV file (including spaces and parentheses).

## Endpoints

- `POST /scrape` - Scrape items by tag
- `GET /health` - Health check endpoint
