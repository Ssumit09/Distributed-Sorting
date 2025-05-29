import os
import json

TRUST_SCORE_FILE = "utils/trust_scores.json"

# Initialize if not exists
if not os.path.exists(TRUST_SCORE_FILE):
    with open(TRUST_SCORE_FILE, 'w') as f:
        json.dump({}, f)

def get_trust_score(ip):
    with open(TRUST_SCORE_FILE, 'r') as f:
        scores = json.load(f)
    return scores.get(ip, 1)

def update_trust_score(ip, success):
    with open(TRUST_SCORE_FILE, 'r') as f:
        scores = json.load(f)
    current_score = scores.get(ip, 1)
    if success and current_score < 3:
        scores[ip] = current_score + 1
    elif not success and current_score > 1:
        scores[ip] = current_score - 1
    with open(TRUST_SCORE_FILE, 'w') as f:
        json.dump(scores, f)

def all_trust_scores():
    with open(TRUST_SCORE_FILE, 'r') as f:
        return json.load(f)

def initialize_trust_score(ip):
    """Add a new worker IP to trust scores if not present."""
    with open(TRUST_SCORE_FILE, 'r') as f:
        scores = json.load(f)
    if ip not in scores:
        scores[ip] = 1  # Default trust score
        with open(TRUST_SCORE_FILE, 'w') as f:
            json.dump(scores, f)
