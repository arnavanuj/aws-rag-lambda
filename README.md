# AWS RAG Lambda

## Introduction

This project is a simple AWS serverless pipeline that reads a PDF from Amazon S3, extracts the text with `PyPDF2`, sends the text to Amazon Bedrock Nova Pro, and returns a short summary.

It solves a common automation problem: turning uploaded documents into AI-generated summaries without managing servers.

## Architecture Overview

Flow:

`Amazon S3 -> AWS Lambda -> PyPDF2 -> Amazon Bedrock (Nova Pro) -> Summary`

When a PDF is uploaded to S3, Lambda is triggered. The function downloads the file, extracts the text, sends part of that text to Bedrock, and logs the summary.

## AWS Services Used

- **Amazon S3**: Stores PDF files and triggers the workflow
- **AWS Lambda**: Runs the document processing logic
- **Amazon Bedrock**: Generates the document summary with Nova Pro

## How It Works

1. A PDF file is uploaded to an S3 bucket.
2. The S3 event triggers the Lambda function.
3. Lambda reads the uploaded file from S3.
4. `PyPDF2` extracts text from the PDF.
5. The extracted text is sent to Amazon Bedrock Nova Pro.
6. Bedrock returns a summary.
7. The summary is printed to CloudWatch logs and returned by the function.

## Prerequisites

- An AWS account
- IAM permissions for S3, Lambda, CloudWatch Logs, and Bedrock
- Bedrock model access enabled for `amazon.nova-pro-v1:0`
- A supported Bedrock region such as `us-east-1` or another region where your model access is enabled
- Python 3.11 for local packaging and CI/CD

## Setup Instructions

### 1. Install dependencies

```bash
pip install -r requirements.txt -t package
```

### 2. Package the Lambda zip

Linux/macOS:

```bash
cp lambda_function.py package/
cd package
zip -r ../function.zip .
```

Windows PowerShell:

```powershell
Copy-Item lambda_function.py package\
Compress-Archive -Path package\* -DestinationPath function.zip -Force
```

### 3. Deploy the Lambda function

```bash
aws lambda update-function-code \
  --function-name pdf-notifier-function \
  --zip-file fileb://function.zip
```

You can also use the included GitHub Actions workflow to deploy automatically on every push to `main`.

## How to Test

1. Upload a PDF file to the configured S3 bucket.
2. Confirm that the Lambda trigger runs.
3. Open CloudWatch Logs for the function.
4. Check for:
   - the decoded file key
   - `TEXT EXTRACTED`
   - the generated summary output

## Challenges Faced

- **IAM permission errors**: Lambda needs the right permissions for S3 reads, bucket listing in some cases, Bedrock invocation, and CloudWatch logging.
- **`NoSuchKey` errors**: S3 event object keys may be URL-encoded, which can break lookups if the key is decoded incorrectly.
- **Encoding issues (`+` vs space)**: Using the wrong decoder can turn valid object keys into invalid paths.
- **Bedrock API schema mismatch**: Different models expect different request payload formats. Nova uses a `messages`-style payload.
- **Region issues**: S3, Lambda, and Bedrock do not always behave well when resources or model access are in different regions.
- **Packaging issues**: Lambda deployments fail if required libraries are missing from the zip file.

## Future Improvements

- Add a proper RAG layer with Amazon OpenSearch or another vector store
- Add a simple UI for uploads and summary viewing
- Add evaluation metrics for summary quality and reliability
