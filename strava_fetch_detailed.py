import requests
import pandas as pd
from pathlib import Path
from strava_utils import get_access_token
import time

DATA_FILE = Path("data/strava_activities_detailed.csv")

def get_all_activity_ids(access_token, per_page=200):
    """Fetch all activity IDs using paginated summary endpoint."""
    
    activities = []
    headers = {"Authorization": f"Bearer {access_token}"}
    page = 1
    
    while True:
        url = f"https://www.strava.com/api/v3/athlete/activities?per_page={per_page}&page={page}"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"Failed to fetch page {page}: {r.status_code}")
            break
        data = r.json()
        if not data:
            break
        activities.extend(data)
        print(f"Fetched page {page}, got {len(data)} activities")
        page += 1
    
    return set(int(activity["id"]) for activity in activities)


def get_activity(access_token, activity_id):
    """Download detailed info for one activity."""
    
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=true"
    r = requests.get(url, headers=headers)
    
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 429:
        print("Hit Strava API limit. Waiting 15 minutes...")
        time.sleep(15 * 60)
        return get_activity(access_token, activity_id)
    else:
        print(f"Failed to fetch activity {activity_id}: {r.status_code}")
        return None


def load_existing(filename=DATA_FILE):
    """Load existing data and return as DataFrame + set of IDs."""
    
    if filename.exists():
        df = pd.read_csv(filename)
        return df, set(df["id"].astype(int).tolist())
    return pd.DataFrame(), set()


def save_detailed(df, filename=DATA_FILE):
    """Save activities to CSV."""
    
    filename.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} activities to {filename}")


if __name__ == "__main__":
    token = get_access_token()

    # Get all activities IDs
    all_ids = get_all_activity_ids(token, per_page=200)
    print(f"Found {len(all_ids)} activities in account.")

    # Read existing
    df_old, existing_ids = load_existing()
    missing_ids = all_ids - existing_ids
    print(f"{len(existing_ids)} already saved, {len(missing_ids)} missing.")

    # Read new
    new_details = []
    for i, act_id in enumerate(missing_ids, start=1):
        detail = get_activity(token, act_id)
        if detail:
            new_details.append(detail)
        if i % 95 == 0:
            print("Pausing to respect Strava API limits (95/100).")
            time.sleep(15 * 60)

    # Save existing and new
    if new_details:
        df_new = pd.json_normalize(new_details)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
        df_all = df_all.drop_duplicates(subset=["id"], keep="last")
        save_detailed(df_all)
    else:
        print("No new detailed activities to add.")
