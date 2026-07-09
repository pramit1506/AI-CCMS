import requests
import json
import time

URL = "http://localhost:8000/api/v1/chat/"

def print_res(res):
    if res.status_code != 200:
        print("Error:", res.text)
        return None
    data = res.json()["data"]
    print(f"Status: {data['conversation_status']}")
    print(f"Response: {data.get('assistant_message')}")
    if "interaction_draft" in data and data["interaction_draft"]:
        draft = data["interaction_draft"]
        print(f"Draft Fields: {', '.join([k for k, v in draft.items() if v])}")
    print("-" * 50)
    return data["conversation_id"]

if __name__ == "__main__":
    print("Starting manual verification...")
    
    # Scenario 1: Log interaction with Dr. Verma, partial fields
    payload = {"user_message": "Log an interaction with Dr. Verma."}
    print("Turn 1: User:", payload["user_message"])
    try:
        res = requests.post(URL, json=payload)
    except Exception as e:
        print("Failed to connect to backend. Is uvicorn running?", e)
        exit(1)
        
    conv_id = print_res(res)
    
    if not conv_id:
        exit(1)
    
    # Scenario 1: provide "Completed"
    payload = {"conversation_id": conv_id, "user_message": "We discussed the new drug. Status is completed. Interaction was today over email."}
    print("Turn 2: User:", payload["user_message"])
    res = requests.post(URL, json=payload)
    print_res(res)
