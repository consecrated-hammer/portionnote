import os
import httpx

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise SystemExit("OPENAI_API_KEY is not set. Add it to your .env before running this test.")

print("Testing OpenAI API connection...")
print("Using API key: [set]")

try:
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": "Say 'API connection successful' in exactly 3 words"}
            ],
            "max_tokens": 10
        },
        timeout=30.0
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"✓ SUCCESS - OpenAI API is working!")
        print(f"Response: {message}")
        print(f"\nModel: {data.get('model')}")
        print(f"Usage: {data.get('usage')}")
    else:
        print(f"✗ FAILED - Status {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"✗ ERROR: {str(e)}")
