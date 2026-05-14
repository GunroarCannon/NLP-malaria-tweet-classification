import pandas as pd
import os
from IPython.display import clear_output

# 1. Load your data
FILE_PATH = 'unique_malaria_tweets.json'
df = pd.read_json(FILE_PATH)
if 'label' not in df.columns: 
    df['label'] = -1

# 2. Define categories
categories = {
    "1": "Symptoms", "2": "Treatment", "3": "Prevention",
    "4": "Misinfo", "5": "Health System", "6": "Personal", 
    "7": "Irrelevant", "8": "Humour"
}

def save_progress():
    df.to_json(FILE_PATH, orient='records', indent=4)
    print(f"💾 Progress saved to {os.path.basename(FILE_PATH)}")

def start_labeling():
    label_count = 0
    
    while True:
        clear_output(wait=True)
        remaining = df[df['label'] == -1]
        
        if remaining.empty:
            save_progress()
            print("🎉 ALL DONE! Every tweet is labeled.")
            break
            
        current_idx = remaining.index[0]
        
        # Display UI
        print(f"--- [ Progress: {len(df) - len(remaining)}/{len(df)} ] ---")
        print(f"Tweet ID: {current_idx}")
        print("-" * 30)
        print(df.at[current_idx, 'text'])
        print("-" * 30)
        
        # Display Options
        print("Options: " + " | ".join([f"[{k}] {v}" for k, v in categories.items()]))
        print("[s] Save & Quit | [Enter] Skip")
        
        # Get user choice
        choice = input("Select a label: ").strip().lower()
        
        if choice == 's':
            save_progress()
            print("Exiting...")
            break
        elif choice in categories:
            df.at[current_idx, 'label'] = int(choice)
            label_count += 1
            # Auto-save every 5 labels
            if label_count >= 5:
                save_progress()
                label_count = 0
        else:
            # Skip or invalid input
            continue

# Launch the tool
start_labeling()
