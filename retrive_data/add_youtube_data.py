import json
import logging
import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import sqlite3
from typing import Dict, List
from datetime import datetime

columns = [
    'date',
    'estimated_minutes_watched',
    'views',
    'likes',
    'subscribers_gained',
    'average_view_duration',
    'average_view_percentage',
    'dislikes',
    'shares'
]
token_file = "token.pickle"
client_secret_file = "client_secret_x.json"
    
def authorize_credentials():
    credentials = None

    if os.path.exists(token_file):
        print("Loading Credentials From File...")
        with open(token_file, "rb") as token:
            credentials = pickle.load(token)
            print(credentials)
            
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing Access Token...")
            credentials.refresh(Request())
        else:
            print("Fetching New Tokens...")
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file,
                scopes=["https://www.googleapis.com/auth/youtube.readonly"]
            )
            flow.run_local_server(port=8090, prompt="consent",
                               authorization_prompt_message="")
            credentials = flow.credentials
            
        with open(token_file, "wb") as f:
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
    if response:
        print("YouTube Analytics data retrieved successfully.")
    return response

def get_latest_date():
    conn = sqlite3.connect('../youtube/yt_analytics.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM youtube_analytics ORDER BY ROWID DESC LIMIT 3")
    # c.execute("PRAGMA table_info(youtube_analytics)")
    # columns = [column[1] for column in c.fetchall()]
    # print(columns)
    row = c.fetchall()
    conn.close()
    
    return row[0] if row else None

def insert_data(yt_data):
    
    conn = sqlite3.connect('../youtube/yt_analytics.db')
    c = conn.cursor()
    
    # Create table if it doesn't exist (using the columns list)
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS youtube_analytics (
        {columns[0]} TEXT PRIMARY KEY,
        {columns[1]} INTEGER,
        {columns[2]} INTEGER,
        {columns[3]} INTEGER,
        {columns[4]} INTEGER,
        {columns[5]} INTEGER,
        {columns[6]} REAL,
        {columns[7]} INTEGER,
        {columns[8]} INTEGER
    )
    """
    c.execute(create_table_sql)
    
    # Process each row of data
    for row in yt_data.get('rows', []):
        day = row[0]  # First column is always date
        
        # Check if this day's data already exists
        c.execute(f"SELECT 1 FROM youtube_analytics WHERE {columns[0]} = ?", (day,))
        exists = c.fetchone()
        
        if not exists:
            try:
                # Generate the INSERT SQL using the columns list
                placeholders = ', '.join(['?'] * len(columns))
                insert_sql = f"""
                INSERT INTO youtube_analytics ({', '.join(columns)})
                VALUES ({placeholders})
                """
                c.execute(insert_sql, row)
                print(f"Inserted data for {day}")
            except sqlite3.Error as e:
                print(f"Error inserting data for {day}: {e}")
        else:
            print(f"Data for {day} already exists - skipping")
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    row = get_latest_date()
    start_date = row[0]
    today = datetime.now().strftime("%Y-%m-%d")
    response = get_yt_analytics(start_date,today)
    insert_data(response)