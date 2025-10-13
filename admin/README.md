# 🛡️ AIDR Bastion Admin Panel

Modern web-based administration interface for AIDR Bastion, built with Streamlit.

## ✨ Features

### 📊 Dashboard
- Real-time statistics and metrics
- Interactive charts and graphs
- Status distribution (Blocked, Notified, Allowed)
- Events timeline visualization
- Top triggered rules analysis
- System health monitoring

### 📋 Rules Management
- Full CRUD operations for detection rules
- Advanced filtering (category, status, search)
- Rule creation with validation
- Enable/disable rules with one click
- Edit existing rules
- Rules statistics and analytics

### 🔍 Events Viewer
- Browse all security events
- Filter by status, flow, and content
- Search in prompt text
- Detailed event inspection
- View triggered rules and pipelines
- Export to CSV/JSON
- Auto-refresh capability

### ⚙️ Settings
- Pipeline flows configuration
- Manager status overview
- System information
- API connection testing
- Documentation links

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

Or install admin-specific packages:

```bash
pip install streamlit plotly pandas requests
```

### 2. Configure Environment (Optional)

Copy the example environment file and customize if needed:

```bash
cd admin
cp env.example .env
# Edit .env with your configuration
```

The admin panel will automatically use these settings:
- `ADMIN_API_BASE_URL` - Base URL of AIDR Bastion API (default: http://localhost:8000)
- `ADMIN_API_PREFIX` - API prefix (default: /api/v1)
- `ADMIN_API_TIMEOUT` - Request timeout in seconds (default: 30)

### 3. Start AIDR Bastion API

Make sure the main API is running:

```bash
# From project root
python server.py
```

API should be available at `http://localhost:8000`

### 4. Launch Admin Panel

```bash
# From project root
streamlit run admin/app.py
```

Or from admin directory:

```bash
cd admin
streamlit run app.py
```

Admin panel will open at `http://localhost:8501`

## 📁 Project Structure

```
admin/
├── app.py                   # Main entry point
├── pages/                   # Streamlit pages
│   ├── 1_📊_Dashboard.py   # Analytics dashboard
│   ├── 2_📋_Rules.py       # Rules management
│   ├── 3_🔍_Events.py      # Events viewer
│   └── 4_⚙️_Settings.py    # System settings
├── utils/
│   └── api_client.py       # API client wrapper
└── README.md               # This file
```

## 🎯 Usage

### Dashboard
- View real-time statistics
- Monitor system health
- Analyze trends with interactive charts
- Check recent activity

### Rules Management
1. Navigate to **📋 Rules** page
2. Use filters to find specific rules
3. Click **➕ Create Rule** to add new rule
4. Click **✏️ Edit** to modify existing rules
5. Use **🔄 Toggle** to enable/disable rules
6. Use **🗑️ Delete** to remove rules

### Events Browser
1. Go to **🔍 Events** page
2. Apply filters (status, flow, limit)
3. Search for specific content
4. Click on events to see details
5. View triggered rules and pipelines
6. Export data as needed

### Settings
1. Open **⚙️ Settings** page
2. Check pipeline flows configuration
3. Monitor manager status
4. Test API connection
5. View system information

## ⚙️ Configuration

### API Connection

The admin panel can be configured in two ways:

**Method 1: Environment Variables (Recommended)**

Create a `.env` file in the `admin/` directory:

```bash
# admin/.env
ADMIN_API_BASE_URL=http://localhost:8000
ADMIN_API_PREFIX=/api/v1
ADMIN_API_TIMEOUT=30
```

The settings will be automatically loaded on startup.

**Method 2: Runtime Configuration**

You can also change settings dynamically through the web interface:

1. Go to **Settings** → **API Config** tab
2. Update Base URL and API Prefix
3. Test connection
4. Save configuration

**Note:** Runtime changes are temporary and will be reset when you restart the admin panel. Use `.env` file for persistent configuration.

### Streamlit Configuration

Create `.streamlit/config.toml` in admin directory:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
enableCORS = false
headless = true

[browser]
gatherUsageStats = false
```

## 🔧 Development

### Adding New Pages

1. Create new file in `admin/pages/`
2. Name format: `N_icon_Name.py` (e.g., `5_🔔_Alerts.py`)
3. Import API client:
   ```python
   from admin.utils.api_client import api
   ```
4. Build your page using Streamlit components

### Extending API Client

Edit `admin/utils/api_client.py` to add new API methods:

```python
class APIClient:
    def new_method(self, param: str) -> Dict:
        """New API method."""
        return self._make_request("GET", f"/endpoint/{param}")
```

## 🐛 Troubleshooting

### "Connection refused"
- Make sure AIDR Bastion API is running on port 8000
- Check if API is accessible: `curl http://localhost:8000/api/v1/events/stats`

### "Module not found"
- Install dependencies: `pip install -r requirements.txt`
- Make sure you're in the correct directory

### "Page not loading"
- Check Streamlit logs in terminal
- Verify all files are in correct locations
- Try restarting Streamlit

### Port already in use
- Change port: `streamlit run app.py --server.port 8502`
- Or kill process using port 8501

## 📊 Performance

### Recommended Settings
- **Events Limit**: 50-100 for optimal performance
- **Auto-refresh**: Use with caution, may impact performance
- **Large datasets**: Use filters to reduce data volume

### Optimization Tips
- Use filters to reduce data volume
- Disable auto-refresh when not needed
- Export data for offline analysis
- Close unused browser tabs

## 🔒 Security

### Important Notes
- Admin panel is for **internal use only**
- No built-in authentication (add reverse proxy with auth)
- API endpoints have no rate limiting by default
- Always use HTTPS in production

### Production Deployment

For production, use authentication:

```bash
# Example with basic auth using nginx
server {
    listen 443 ssl;
    server_name admin.yourdomain.com;

    auth_basic "AIDR Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:8501;
    }
}
```

## 📚 Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Charts](https://plotly.com/python/)
- [AIDR Bastion API Docs](http://localhost:8000/docs)

## 🤝 Contributing

When adding new features to admin panel:
1. Follow existing code structure
2. Use type hints
3. Add docstrings
4. Test with real API data
5. Update this README

## 📝 License

Same as main AIDR Bastion project (LGPL-3.0)

## 🆘 Support

For issues and questions:
- Check main project README
- Review API documentation
- Test API connection first
- Check Streamlit logs

---

Built with ❤️ using Streamlit
