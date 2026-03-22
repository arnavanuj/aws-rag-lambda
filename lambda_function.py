import json
import urllib.parse
import boto3
import io
from PyPDF2 import PdfReader

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event, context):

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'],
        encoding='utf-8'
    )

    print(f"Processing file: {key}")

    # Read PDF
    response = s3.get_object(Bucket=bucket, Key=key)
    pdf_bytes = response['Body'].read()

    # Extract text
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    print("TEXT EXTRACTED")

    # Call Bedrock Nova Pro
    response = bedrock.invoke_model(
    modelId="amazon.nova-pro-v1:0",
    body=json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": f"Summarize this document:\n\n{text[:3000]}"
                    }
                ]
            }
        ],
        "inferenceConfig": {
            "max_new_tokens": 300,
            "temperature": 0.5
        }    }))

    result = json.loads(response['body'].read())

    summary = result['output']['message']['content'][0]['text']

    print("SUMMARY:")
    print(summary)

    return summary