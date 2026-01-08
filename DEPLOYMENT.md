# Deployment Guide

This guide will help you deploy the Roblox Catalog Scraper API on a Linux server using Nginx and systemd.

## Prerequisites

- Ubuntu/Debian server with root access
- Domain name (optional, but recommended for SSL)
- Python 3.8 or higher

## Installation Steps

### 1. Update System and Install Dependencies

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx
```

### 2. Create Application Directory

```bash
sudo mkdir -p /var/www/catalog
sudo chown $USER:$USER /var/www/catalog
```

### 3. Upload Application Files

Copy all project files to the server:

```bash
# From your local machine
scp -r * user@your-server:/var/www/catalog/
```

Or clone from git:

```bash
cd /var/www/catalog
git clone <your-repo-url> .
```

### 4. Set Up Python Virtual Environment

```bash
cd /var/www/catalog
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### 5. Configure Environment Variables

Set authentication credentials:

```bash
# Create environment file
sudo nano /etc/environment

# Add these lines (replace with strong credentials):
API_USERNAME="your_secure_username"
API_PASSWORD="your_secure_password"

# Or add to the systemd service file directly (see step 6)
```

### 6. Configure Systemd Service

```bash
# Copy service file
sudo cp roblox-catalog-api.service /etc/systemd/system/

# Edit the service file to match your setup
sudo nano /etc/systemd/system/roblox-catalog-api.service
# Update User, Group, WorkingDirectory if needed
# Add Environment variables for authentication:
#   Environment="API_USERNAME=your_username"
#   Environment="API_PASSWORD=your_password"

# Set proper ownership
sudo chown -R www-data:www-data /var/www/catalog

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable roblox-catalog-api
sudo systemctl start roblox-catalog-api

# Check status
sudo systemctl status roblox-catalog-api
```

### 7. Configure Nginx

```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/catalog-api

# Edit the configuration
sudo nano /etc/nginx/sites-available/catalog-api
# Update server_name to your domain or IP

# Create symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/catalog-api /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 8. Configure Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 9. Test the API

```bash
curl -X POST http://your-domain.com/scrape \
  -u your_username:your_password \
  -H "Content-Type: application/json" \
  -d '{"tag": "Hair"}'
```

## Optional: Set Up SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Certbot will automatically configure nginx for SSL
# Or you can manually uncomment the SSL section in nginx.conf
```

## Monitoring and Logs

### View API Logs

```bash
# Service logs
sudo journalctl -u roblox-catalog-api -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Service Management Commands

```bash
# Start service
sudo systemctl start roblox-catalog-api

# Stop service
sudo systemctl stop roblox-catalog-api

# Restart service
sudo systemctl restart roblox-catalog-api

# Check status
sudo systemctl status roblox-catalog-api

# View logs
sudo journalctl -u roblox-catalog-api -n 100
```

## Updating the Application

```bash
# Stop the service
sudo systemctl stop roblox-catalog-api

# Update code
cd /var/www/catalog
git pull  # or upload new files

# Update dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# Restart the service
sudo systemctl start roblox-catalog-api
```

## Performance Tuning

### Adjust Gunicorn Workers

Edit `/etc/systemd/system/roblox-catalog-api.service`:

```bash
# Formula: (2 x CPU cores) + 1
# For 4 CPU cores: --workers 9
ExecStart=/var/www/catalog/venv/bin/gunicorn --workers 9 --bind 127.0.0.1:5000 api:app
```

### Nginx Rate Limiting

The default configuration limits requests to 10 per second with a burst of 20. Adjust in `nginx.conf`:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status and logs
sudo systemctl status roblox-catalog-api
sudo journalctl -u roblox-catalog-api -n 50

# Check file permissions
ls -la /var/www/catalog

# Ensure virtual environment is correct
/var/www/catalog/venv/bin/python --version
```

### Nginx 502 Bad Gateway

```bash
# Check if the service is running
sudo systemctl status roblox-catalog-api

# Check if gunicorn is listening on correct port
sudo netstat -tlnp | grep 5000

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Timeout Errors

If scraping requests timeout, increase the timeout values in `nginx.conf`:

```nginx
proxy_connect_timeout 120s;
proxy_send_timeout 120s;
proxy_read_timeout 180s;
```

## Security Considerations

1. **Authentication**: Basic auth is enabled - use strong credentials and HTTPS
2. **Firewall**: Only allow necessary ports (80, 443, SSH)
3. **Rate Limiting**: Configured in nginx to prevent abuse
4. **User Permissions**: Service runs as `www-data` with limited privileges
5. **SSL**: Always use HTTPS in production to protect credentials
6. **Environment Variables**: Store credentials securely, never in code
7. **CORS**: Restrict origins in production (currently allows all)

## Production Checklist

- [ ] Strong authentication credentials set
- [ ] SSL certificate installed
- [ ] Domain configured
- [ ] Firewall rules set
- [ ] Rate limiting configured
- [ ] Service auto-starts on boot
- [ ] Logs monitored
- [ ] Backups configured
- [ ] CORS properly configured
- [ ] Error handling tested
