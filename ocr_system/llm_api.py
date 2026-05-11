import requests

api_key = "sk-SsNrJQl7FaNMhtK1im0jvg"
url = "https://qwen-api.kalima-ocr.com/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "qwen-3.5-35b",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())