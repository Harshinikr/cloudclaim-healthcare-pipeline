import json
import boto3
import os
import logging
from datetime import datetime, timezone

# Set up structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients outside the handler for connection reuse
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Read table name from environment variable — never hardcode resource names
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'cloudclaim-claims')

# Required fields every valid healthcare claim must have
REQUIRED_FIELDS = [
    'claim_id',
    'patient_id',
    'provider_id',
    'procedure_code',
    'diagnosis_code',
    'claim_amount',
    'service_date'
]


def validate_claim(claim: dict) -> tuple[bool, list]:
    """
    Validate that a claim contains all required fields with non-empty values.
    Returns (is_valid, list_of_missing_fields).
    """
    missing = [field for field in REQUIRED_FIELDS if not claim.get(field)]
    return len(missing) == 0, missing


def handler(event, context):
    """
    Lambda entry point. Triggered by S3 PutObject events.
    Reads claim JSON from S3, validates it, writes to DynamoDB.
    """
    logger.info("CloudClaim ingestion Lambda invoked")

    # S3 events can contain multiple records (batch uploads)
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        logger.info(f"Processing file: s3://{bucket}/{key}")

        try:
            # Read the claim file from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            claim = json.loads(response['Body'].read().decode('utf-8'))

            # Validate required fields
            is_valid, missing_fields = validate_claim(claim)

            if not is_valid:
                logger.warning(
                    f"Claim validation failed for {key}. "
                    f"Missing fields: {missing_fields}"
                )
                # Write a REJECTED record to DynamoDB so we have an audit trail
                table = dynamodb.Table(TABLE_NAME)
                table.put_item(Item={
                    'claim_id': claim.get('claim_id', key),
                    'status': 'REJECTED',
                    'rejection_reason': f"Missing required fields: {missing_fields}",
                    'source_file': key,
                    'processed_at': datetime.now(timezone.utc).isoformat()
                })
                continue

            # Build the DynamoDB item from the validated claim
            table = dynamodb.Table(TABLE_NAME)
            item = {
                'claim_id': claim['claim_id'],
                'patient_id': claim['patient_id'],
                'provider_id': claim['provider_id'],
                'procedure_code': claim['procedure_code'],
                'diagnosis_code': claim['diagnosis_code'],
                'claim_amount': str(claim['claim_amount']),
                'service_date': claim['service_date'],
                'status': 'RECEIVED',
                'source_file': key,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }

            table.put_item(Item=item)

            logger.info(
                f"Successfully processed claim {claim['claim_id']} "
                f"— status: RECEIVED"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {key}: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error processing {key}: {str(e)}")
            raise

    return {
        'statusCode': 200,
        'body': json.dumps('Claims processing complete')
    }