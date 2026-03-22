# FAQ

## Section 1: Questions from this project

### Why does S3 give a `NoSuchKey` error?

This usually means the object key Lambda is using does not exactly match the real key in S3. In event-driven flows, the most common cause is encoding. The key in the S3 event is URL-encoded, so characters like spaces and plus signs can be represented differently from what you expect.

It can also happen when:

- the file was deleted after the event fired
- the Lambda is reading the wrong bucket
- the uploaded filename contains special characters
- the decoded key is different from the real stored object key

In practice, logging the raw event key and the decoded key is the fastest way to debug it.

### What is the difference between `unquote` and `unquote_plus`?

`unquote` decodes standard URL-encoded characters like `%20`, but it leaves `+` as `+`.

`unquote_plus` also converts `+` into a space.

This matters because S3 event keys often behave like form-encoded values. If the original filename has spaces, `unquote_plus` is usually the safer choice. If the original key really contains a plus sign as a literal character, using the wrong decoder can change the key and cause `NoSuchKey`.

The practical lesson is simple: always compare the final decoded key with the actual object key stored in S3.

### Why does Lambda need `s3:ListBucket` permission?

For a simple `GetObject`, Lambda mainly needs `s3:GetObject` on the object path. But in real projects, `s3:ListBucket` often becomes necessary for debugging, validation, or prefix-based operations.

Without it, some flows fail in confusing ways because the function cannot confirm whether a key exists or inspect bucket contents when troubleshooting.

If your code only fetches one known object, you may not strictly need `s3:ListBucket`, but teams often add it to reduce operational friction.

### Why does Bedrock fail with `AccessDenied`?

This usually means one of three things:

- the IAM role does not allow `bedrock:InvokeModel`
- model access was not enabled in the AWS account
- the request is being sent to the wrong region

Bedrock permissions are not enough on their own. You also need model access approved in the target region. Many teams lose time here because the IAM policy looks correct while the model is still unavailable in that region.

### Why does Nova require the `messages` format?

Bedrock models do not all use the same input schema. Nova models expect a chat-style payload with `messages`, while other models may expect a simpler prompt field or a different wrapper structure.

If you send the wrong schema, the call fails even though the endpoint and permissions are correct. This is why copying a Titan payload into Nova code often breaks immediately.

### What is the difference between Titan and Nova models?

Titan and Nova are different model families with different capabilities and request formats.

In practical terms:

- Titan examples often use different payload fields from Nova
- Nova is commonly used with `messages` content blocks
- output parsing can differ between models
- model IDs are different, so region availability and access can also differ

The main takeaway is that changing the model is not just a one-line swap. You usually need to update both the request body and the response parsing.

### Why does region matter in Bedrock?

Bedrock is region-specific. A model may be enabled in one region and unavailable in another. Your Lambda may run successfully, but the Bedrock call can still fail if:

- the model is not supported in that region
- your account does not have access in that region
- the SDK client is pointing somewhere different from your Lambda deployment region

This is why `us-east-1` vs `ap-southeast-2` can completely change the result.

### Why does deployment succeed but the function does not run?

A successful deployment only means AWS accepted the zip file. It does not mean the runtime works.

Common reasons the function still fails:

- missing Python dependencies inside the zip
- wrong handler name
- missing IAM permissions
- timeout or memory limits
- runtime errors that only appear in CloudWatch Logs

Always verify deployment and execution separately.

### Why does zip packaging fail in Lambda?

The most common reason is that the deployment package does not include third-party libraries. Lambda only has the standard runtime plus AWS-managed libraries. If `PyPDF2` is not packaged into the zip, imports fail at runtime.

Other common issues:

- zipping the parent folder instead of the contents
- incorrect folder structure
- packaging on one OS and assuming the same command works everywhere

### Why does the Git Bash `zip` command fail on Windows?

Many Windows setups do not include a native `zip` command in Git Bash, or the command behaves differently from Linux. That causes confusing packaging failures even though the same instructions work in CI or on macOS/Linux.

On Windows, `Compress-Archive` in PowerShell is usually more reliable for simple Lambda packaging.

## Section 2: Advanced AWS AI Questions

### What is the difference between serverless and container-based AI deployment?

Serverless deployment, like S3 plus Lambda plus Bedrock, is best when traffic is event-driven, workloads are bursty, and you want low operational overhead.

Container-based deployment is better when you need:

- long-running processes
- custom system packages
- GPU workloads
- tight control over networking and scaling behavior

For lightweight PDF summarization, serverless is usually faster to build and cheaper to maintain.

### How can you optimize LLM cost in AWS?

The biggest cost levers are prompt size, model choice, and invocation frequency.

Practical ways to reduce cost:

- send only the most relevant text, not the entire document
- chunk large files before calling the model
- use smaller or cheaper models where possible
- cache repeat summaries
- avoid calling the model for blank, scanned, or low-value documents

Cost control is mostly a data-filtering problem, not just a model problem.

### When should you use Textract instead of LLM OCR?

Use Textract when the document is scanned, image-heavy, form-based, or requires structured field extraction.

Use an LLM after OCR when you want reasoning, summarization, classification, or question answering over the extracted text.

In production, the common pattern is:

`scanned PDF -> Textract/OCR -> cleaned text -> LLM`

### How do you design a production RAG system on AWS?

A production RAG system usually adds:

- a document ingestion pipeline
- text chunking and metadata tagging
- embeddings generation
- a vector store such as OpenSearch
- retrieval before generation
- monitoring for accuracy, latency, and cost

This project is a strong starting point for ingestion and summarization, but full RAG needs retrieval, indexing, and evaluation layers.

### How should large PDFs be handled?

Large PDFs should not be sent as one giant prompt. That increases latency, cost, and failure risk.

A better pattern is:

1. Extract text page by page
2. Chunk the content
3. Summarize each chunk
4. Merge the chunk summaries into a final summary

This is easier to scale and more reliable than one oversized Bedrock request.

### How do you handle concurrency in Lambda?

Concurrency matters when many files land in S3 at the same time. Each upload can trigger a separate Lambda execution.

To handle that safely:

- set reserved concurrency if you need hard limits
- monitor Bedrock throttling and retry behavior
- keep functions idempotent
- use dead-letter queues or event destinations for failures
- watch downstream limits, not just Lambda scaling

The real bottleneck is often the AI service or document size, not Lambda itself.

## Section 3: Scenario-based Questions

### What if the PDF is scanned instead of text-based?

`PyPDF2` works best for text-based PDFs. For scanned PDFs, text extraction may return little or nothing because the content is stored as images.

In that case, add an OCR step such as Amazon Textract before sending the content to Bedrock.

### What if the file size is large?

Large files can cause slow extraction, large prompts, high Bedrock cost, and Lambda timeout risk.

The safest response is to chunk the document, summarize incrementally, and increase Lambda timeout only when needed.

### What if Lambda times out?

Timeouts usually point to one of these problems:

- PDF extraction is too slow
- the file is too large
- the Bedrock response is slow
- retries or network calls are stacking up

Increase the timeout if needed, but also reduce the work done in one invocation. Architectural fixes are usually better than simply raising limits.

### What if Bedrock is unavailable in the target region?

You have two main options:

- move the workload to a region where the model is available
- switch to a model that is supported in your current region

Do not assume model availability is global. Always confirm region support before deployment.

### What if the S3 trigger fails?

If uploads are not invoking Lambda:

- confirm the bucket notification is configured
- confirm the Lambda resource policy allows S3 invocation
- check whether the event filter matches the uploaded file type
- verify the upload actually happened in the expected bucket and prefix

This is one of the easiest issues to miss because the code can be correct while the trigger wiring is wrong.
