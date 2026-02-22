# Roblox Catalog Scraper API

A Python Flask API that scrapes Roblox catalog items by tag and returns item IDs.

## Features

- Accepts requests with a tag in the payload (head, shirt, pants, etc.)
- Scrapes data from Roblox catalog API
- Handles pagination automatically using `nextPageCursor`
- **Configurable result limit** — request any number of assets (default 500)
- **End-detection** — stops early when all items of a category have been collected, response includes `reached_end: true`
- **24-hour in-memory cache** — repeat requests are served instantly; the response includes `cached: true/false`
- Uses 1-second delay between paginated requests to avoid rate-limiting

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Configure Authentication (Optional)

By default, the API uses basic authentication with:
- Username: `arthur`
- Password: `changeme123`

To change credentials, set environment variables:

```bash
export API_USERNAME=your_username
export API_PASSWORD=your_password
```

### Start the server

```bash
python api.py
```

The server will run on `http://localhost:5000`

### Make a request

Basic request (defaults to 500 items):

```bash
curl -X POST http://localhost:5000/scrape \
  -u arthur:changeme123 \
  -H "Content-Type: application/json" \
  -d '{"tag": "Hair"}'
```

Request with a custom limit (e.g. grab all faces, up to 10 000):

```bash
curl -X POST http://localhost:5000/scrape \
  -u arthur:changeme123 \
  -H "Content-Type: application/json" \
  -d '{"tag": "Classic Faces", "limit": 10000}'
```

### Request payload

| Field   | Type   | Required | Default | Description                          |
|---------|--------|----------|---------|--------------------------------------|
| `tag`   | string | yes      | —       | Category tag (see list below)        |
| `limit` | int    | no       | 500     | Max number of asset IDs to retrieve  |

### Response format

```json
{
  "ids": [123456, 789012],
  "count": 487,
  "tag": "Classic Faces",
  "limit": 10000,
  "reached_end": true,
  "cached": false
}
```

| Field         | Description                                                         |
|---------------|---------------------------------------------------------------------|
| `ids`         | Array of item IDs                                                   |
| `count`       | Number of IDs returned                                              |
| `tag`         | The tag that was requested                                          |
| `limit`       | The limit that was used                                             |
| `reached_end` | `true` when every available item in the category has been collected |
| `cached`      | `true` when the response was served from the 24-hour cache          |
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

1. API receives a POST request with a tag and optional limit
2. Checks the 24-hour in-memory cache — if a matching result exists, returns it immediately
3. Looks up the corresponding taxonomy ID from `taxonomy_mapping.csv`
4. Makes requests to Roblox catalog API with limit=120 (maximum allowed by Roblox)
5. Uses `nextPageCursor` to fetch additional pages until the requested limit is reached **or** there are no more items
6. Waits 1 second between paginated requests to avoid rate limiting
7. Caches the result and returns it

**Note:** Tags are case-sensitive and must match exactly as listed in the CSV file (including spaces and parentheses).

## Endpoints

- `POST /scrape` — Scrape items by tag (requires authentication)
- `GET /health` — Health check endpoint (no authentication required)

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for instructions on deploying this API to a production server with Nginx and systemd.
