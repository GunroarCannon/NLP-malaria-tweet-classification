import pandas as pd
import os

UNIQUE_FILE = "unique_malaria_tweets.json" # Switched extension
SOURCE_FILE = "malaria_tweets.jsonl"

if os.path.exists(UNIQUE_FILE):
    print(f"--- {UNIQUE_FILE} exists. Loading unique data. ---")
    df_unique = pd.read_json(UNIQUE_FILE)
else:
    print("--- Cleaning and deduplicating... ---")
    df = pd.read_json(SOURCE_FILE, lines=True)
    print(df.shape)
    # Selection and Renaming
    df = df[["text", "created_at", "author", "views", "favorite_count","is_reply","is_quote"]].copy()
    df.rename(columns={"created_at": "date", "author": "user", "favorite_count": "likes"}, inplace=True)
    
    # Cleaning
    df['text'] = df['text'].str.strip('"').str.strip()
    df_unique = df.drop_duplicates(subset=['text']).copy()
    df_unique["likes"] = pd.to_numeric(df_unique["likes"], errors='coerce').fillna(0)
    
    # SAVE AS JSON
    # orient='records' makes it a list of dictionaries: [{...}, {...}]
    # indent=4 makes it pretty-printed
    df_unique.to_json(UNIQUE_FILE, orient='records', indent=4, force_ascii=False)
    print(f"--- Saved {len(df_unique)} unique tweets to {UNIQUE_FILE} ---")

print(df_unique.head())