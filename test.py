import json
from lambda_function import lambda_handler

with open("event.json") as f:
    event = json.load(f)

response = lambda_handler(event, None)
print("FINAL RESPONSE:", response)