import json
import logging
import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from mcp.server.fastmcp import FastMCP
import sqlite3
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("hello-world-mcp")

# Initialize FastMCP server
mcp = FastMCP("youtube")

def authorize_credentials():
    credentials = None

    if os.path.exists("token.pickle"):
        print("Loading Credentials From File...")
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)
            print(credentials)
            
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing Access Token...")
            credentials.refresh(Request())
        else:
            print("Fetching New Tokens...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret_x.json",
                scopes=["https://www.googleapis.com/auth/youtube.readonly"]
            )
            flow.run_local_server(port=8090, prompt="consent",
                               authorization_prompt_message="")
            credentials = flow.credentials
            
        with open("token.pickle", "wb") as f:
            print("Saving Credentials for Future Use...")
            pickle.dump(credentials, f)
    return credentials

def get_daily_channel_metrics(youtube_analytics_client, start_date, end_date):
    response = youtube_analytics_client.reports().query(
        ids='channel==MINE',
        startDate=start_date,
        endDate=end_date,
        metrics='estimatedMinutesWatched,views,likes,subscribersGained,'
                'averageViewDuration,averageViewPercentage,dislikes,shares',
        dimensions='day',
        sort='day'
    ).execute()
    return response

def get_yt_analytics(start_date,end_date):
    "Return raw json data of youtube analytics"
    credentials = authorize_credentials()
    youtubeAnalytics = build("youtubeAnalytics", "v2", credentials=credentials)
    response = get_daily_channel_metrics(youtubeAnalytics, start_date, end_date)
    print(response)
    return response

class YouTubeAnalyticsDB:
    def __init__(self):
        self.conn = sqlite3.connect('yt_analytics.db')
    
    def query(self, sql: str) -> List[Dict]:
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    
    def close(self):
        self.conn.close()
        
@mcp.tool()
def query_yt_analytics(sql_query: str, start_date: str = None, end_date: str = None):
    """
    Execute SQL queries on YouTube Analytics data with optional date filtering.
    
    Parameters:
    - sql_query: Valid SQL query string (SELECT only)
    - start_date: Optional start date for filtering (YYYY-MM-DD format)
    - end_date: Optional end date for filtering (YYYY-MM-DD format)
    
    Available columns: 
        date, estimated_minutes_watched, views, likes, 
        subscribers_gained, average_view_duration,
        average_view_percentage, dislikes, shares
    
    Example queries:
    - Without dates: "SELECT SUM(views) AS total_views FROM youtube_analytics"
    - With hardcoded dates: "SELECT * FROM youtube_analytics WHERE date BETWEEN '2024-01-01' AND '2024-12-31'"
    - Using parameters: "SELECT * FROM youtube_analytics WHERE date BETWEEN '{start_date}' AND '{end_date}'"
    - Mixed approach: "SELECT date, views FROM youtube_analytics WHERE date >= '{start_date}' ORDER BY views DESC"
    """
    db = YouTubeAnalyticsDB()
    try:
        # Validate query
        sql_query = sql_query.strip()
        if not sql_query.upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        
        # Prepare parameters for formatting
        format_params = {}
        if start_date:
            format_params['start_date'] = start_date
        if end_date:
            format_params['end_date'] = end_date
        
        # Format the query if parameters are present
        try:
            formatted_query = sql_query.format(**format_params) if format_params else sql_query
        except KeyError as e:
            raise ValueError(f"Missing parameter in query: {e}. Available parameters: start_date, end_date")
            
        results = db.query(formatted_query)
        return {"success": True, "results": results}
    finally:
        db.close()

if __name__ == "__main__":
    # Log server startup
    logger.info("Starting Hello World MCP Server...")
    
    # Initialize and run the server
    mcp.run(transport="stdio")
    
    logger.info("Server stopped")