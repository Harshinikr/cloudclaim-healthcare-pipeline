# CloudClaim — Serverless Healthcare Claims Pipeline

I built CloudClaim to solve a real problem I saw firsthand working at Cigna and Anthem — healthcare claims processing is complex, high-stakes, and unforgiving. A single lost claim means a provider doesn't get paid. A missed validation means bad data enters the system. I wanted to build something that handles this correctly, the way production systems at real insurers do.

CloudClaim is a fully serverless, event-driven pipeline that receives healthcare insurance claims, validates them, applies business rules, stores the results, and alerts the claims team — all automatically, with zero data loss guaranteed.

---

## The Problem It Solves

When a doctor treats a patient, the hospital submits a claim to the insurance company. That claim contains structured information — who the patient is, who the provider is, what procedure was performed, what diagnosis was made, and how much it costs. At companies like Cigna and Anthem, millions of these arrive every day. They need to be validated, processed, and either approved or rejected — reliably, at scale, with a full audit trail.

That's exactly what this pipeline does.

---

## How a Claim Moves Through the System

A hospital uploads a claim as a JSON file to an encrypted S3 bucket. The moment that file lands, an event fires automatically and wakes up the ingestion Lambda function. Lambda reads the file, checks that all required fields are present, and places the claim onto an SQS queue. From that moment on, the claim cannot be lost — even if something crashes downstream, SQS holds it safely and retries automatically.

The rules engine Lambda picks the claim off the queue and applies real healthcare validation rules — checking the procedure code is a valid CPT format, the diagnosis code follows ICD-10 standards, the amount is within acceptable limits, and the service date isn't in the future. If the claim passes all rules, it's written to DynamoDB as APPROVED. If it fails, it's written as REJECTED with specific reasons listed, and an SNS notification fires instantly to the claims team's inbox.

Any claim can be queried at any time through a REST API that sits behind API Gateway.

---

## The Business Rules

These mirror real validation logic used by US health insurers:

Claim amounts must fall between $1 and $50,000 — this catches data entry errors and flags potential fraud. Procedure codes must be exactly five digits, which is the standard CPT format used across the US healthcare system. Diagnosis codes must follow the ICD-10 pattern — a letter followed by digits and optional decimal characters. And service dates cannot be in the future, because you cannot bill for care that hasn't happened yet.

---

## Why Each Technology Was Chosen

Lambda runs the processing logic because there are no servers to manage, it scales to zero when idle, and you pay only for the milliseconds it runs. SQS sits between the two Lambda functions because it guarantees delivery — a claim that enters the queue will be processed or it will end up in the Dead Letter Queue for human review, but it will never silently disappear. DynamoDB stores the claims because it handles millions of records with millisecond reads and requires no schema management. SNS sends rejection alerts because it decouples the notification logic — Lambda just publishes an event and SNS handles delivery to whoever needs to know. Terraform defines all of this as code so the entire stack can be created or destroyed with a single command.

---

## Security and Compliance

Every design decision was made with HIPAA in mind. The S3 bucket is encrypted at rest with AES-256 and has all public access blocked. IAM permissions follow least-privilege — each Lambda has only the exact permissions it needs, scoped to the specific resource ARN. No credentials are ever hardcoded. Every claim, approved or rejected, is written to DynamoDB with a full timestamp and audit trail.

---

## Testing

The business rules are fully covered by unit tests that run in under two seconds without any AWS connection. Eight test cases cover valid claims, invalid amounts, bad procedure codes, invalid diagnosis codes, future service dates, and multiple simultaneous violations.

---

## Infrastructure as Code

All 22 AWS resources are defined in Terraform across nine configuration files. The entire pipeline — S3 bucket, DynamoDB table, three Lambda functions, SQS queue, Dead Letter Queue, SNS topic, API Gateway, and all IAM policies — can be provisioned from scratch or torn down completely with a single command.

---

## About Me

I'm Harshini Kulandaisamy Ramesh, a software engineer completing my MS in Software Engineering at Arizona State University with a 3.9 GPA, graduating May 2026. My background in healthcare at Cigna and Anthem gave me real understanding of claims processing, HIPAA requirements, and why reliability matters so much in this domain. I built CloudClaim to bring that domain knowledge together with modern AWS serverless architecture.

[LinkedIn](https://www.linkedin.com/in/harshini-k-r-2173191ab/) · [GitHub](https://github.com/Harshinikr)

