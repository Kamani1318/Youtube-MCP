# YouTube Analytics Data Pipeline

This project retrieves YouTube channel analytics data using the YouTube Analytics API and stores it in a SQLite database for further analysis.

## Prerequisites

- Python 3.6 or higher
- Google account with access to YouTube channel
- Basic understanding of Google Cloud Platform

## Setup Instructions

### 1. Set up Google Cloud Project and Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs for your project:
   - YouTube Analytics API
   - YouTube Data API v3

### 2. Create OAuth 2.0 Credentials

1. In your Google Cloud Console, navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" and select "OAuth client ID"
3. Select application type "Desktop app"
4. Give your client a name (e.g., "YouTube Analytics Client")
5. Click "Create"
6. Download the JSON file containing your client secrets
7. Rename the downloaded file to `client_secret_x.json` and place it in your project root directory

### 3. Python Environment Setup

1. Python Version 3.12.9 needed

2. Install required packages:
   ```bash
   pip install -r recquirements.txt
   ```

## Running the Application

1. First run (authentication):
   ```bash
   python retrive_data/add_youtube_data.py
   ```
   - This will open a browser window asking you to authenticate
   - Grant permissions to your YouTube channel
   - The credentials will be saved in `token.pickle` for future use

2. Subsequent runs:
   - The script will use the saved credentials
   - It will automatically refresh tokens when needed

## Database Setup

The script automatically creates a SQLite database file at `../youtube/yt_analytics.db` with the following schema:

```sql
CREATE TABLE youtube_analytics (
    date TEXT PRIMARY KEY,
    estimated_minutes_watched INTEGER,
    views INTEGER,
    likes INTEGER,
    subscribers_gained INTEGER,
    average_view_duration INTEGER,
    average_view_percentage REAL,
    dislikes INTEGER,
    shares INTEGER
)
```

## MCP Server

1. Install uv in your directory

2. Python version 3.12.9 recquired

3. Run script
```bash
uv run youtube/main.py
```


## Important Files

- `retrive_data/client_secret_x.json`: Your OAuth 2.0 client credentials (keep this secure)
- `retrive_datatoken.pickle`: Stores your authentication tokens (do not share)
- `youtube/yt_analytics.db`: SQLite database file with your analytics data

## Troubleshooting

- If you get authentication errors, delete `token.pickle` and run the script again
- Get another client_secrets.json file if the API doesn't work after a few days.
- Ensure your Google Cloud project has the required APIs enabled
- Make sure your OAuth consent screen is properly configured in Google Cloud Console
