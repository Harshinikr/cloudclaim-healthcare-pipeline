import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3', region_name='us-east-1')
sqs_client = boto3.client('sqs', region_name='us-east-1')

SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL', '')

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
    missing = [field for field in REQUIRED_FIELDS if not claim.get(field)]
    return len(missing) == 0, missing


def handler(event, context):
    logger.info("CloudClaim ingestion Lambda invoked")

    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        logger.info(f"Processing file: s3://{bucket}/{key}")

        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            claim = json.loads(response['Body'].read().decode('utf-8'))

            is_valid, missing_fields = validate_claim(claim)

            if not is_valid:
                logger.warning(
                    f"Claim {key} missing required fields: {missing_fields}"
                )
                continue

            sqs_client.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(claim),
                MessageAttributes={
                    'source_file': {
                        'StringValue': key,
                        'DataType': 'String'
                    }
                }
            )

            logger.info(
                f"Claim {claim['claim_id']} queued successfully"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {key}: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error processing {key}: {str(e)}")
            raise

    return {
        'statusCode': 200,
        'body': json.dumps('Ingestion complete')
    }