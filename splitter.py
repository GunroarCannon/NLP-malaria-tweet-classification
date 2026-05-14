import json

# Read the JSONL file and split into replies and non-replies
replies = []
non_replies = []

filename = "unique_malaria_tweets.json"
import pandas as pd
pp = pd.read_json(filename).to_dict(orient="records")
#print(open(filename,"r+").read())
if 1:
        #jj = json.load(open(filename))
        print(pp)
        for tweet in pp:
            #tweet = json.loads(line)
            tweet["date"] = str(tweet["date"])  # Ensure date is a string
            if tweet.get('is_reply', False):
                replies.append(tweet)
            else:
                non_replies.append(tweet)
        # except json.JSONDecodeError:
        #     print(f"Skipping malformed line: {line[:50]}")

# Write replies to file
with open('_replies.jsonl', 'w', encoding='utf-8') as f:
    for tweet in replies:
        f.write(json.dumps(tweet) + '\n')

# Write non-replies to file
with open('_non_replies.jsonl', 'w', encoding='utf-8') as f:
    for tweet in non_replies:
        f.write(json.dumps(tweet) + '\n')

print(f"Split complete!")
print(f"Replies: {len(replies)} tweets saved to _replies.jsonl")
print(f"Non-replies: {len(non_replies)} tweets saved to _non_replies.jsonl")
