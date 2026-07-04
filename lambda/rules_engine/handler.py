import json
import boto3
import os
import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sns_client = boto3.client('sns', region_name='us-east-1')

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'cloudclaim-claims')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


def apply_business_rules(claim: dict) -> tuple[bool, list]:
    """
    Apply healthcare business rules to a validated claim.
    Returns (is_approved, list_of_rejection_reasons).
    """
    reasons = []

    # Rule 1: Claim amount must be between $1 and $50,000
    try:
        amount = float(claim.get('claim_amount', 0))
        if amount <= 0:
            reasons.append("Claim amount must be greater than $0")
        elif amount > 50000:
            reasons.append(
                f"Claim amount ${amount} exceeds maximum allowed $50,000"
            )
    except (ValueError, TypeError):
        reasons.append("Claim amount is not a valid number")

    # Rule 2: Procedure code must be 5 digits (CPT code format)
    procedure_code = str(claim.get('procedure_code', ''))
    if not re.match(r'^\d{5}$', procedure_code):
        reasons.append(
            f"Procedure code '{procedure_code}' is not valid CPT format "
            f"(must be 5 digits)"
        )

    # Rule 3: Diagnosis code must match ICD-10 format (e.g. J06.9, A01.1)
    diagnosis_code = str(claim.get('diagnosis_code', ''))
    if not re.match(r'^[A-Z][0-9]{2}\.?[0-9A-Z]{0,4}$', diagnosis_code):
        reasons.append(
            f"Diagnosis code '{diagnosis_code}' is not valid ICD-10 format"
        )

    # Rule 4: Service date cannot be in the future
    try:
        service_date = datetime.strptime(
            claim.get('service_date', ''), '%Y-%m-%d'
        )
        if service_date.date() > datetime.now(timezone.utc).date():
            reasons.append(
                f"Service date {claim['service_date']} cannot be in the future"
            )
    except ValueError:
        reasons.append(
            f"Service date '{claim.get('service_date')}' "
            f"is not valid format (YYYY-MM-DD)"
        )

    return len(reasons) == 0, reasons


def publish_rejection_alert(claim: dict, rejection_reasons: list):
    """Publish rejection alert to SNS topic."""
    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not set — skipping alert")
        return

    message = (
        f"CLAIM REJECTED\n\n"
        f"Claim ID:      {claim['claim_id']}\n"
        f"Patient ID:    {claim['patient_id']}\n"
        f"Provider ID:   {claim['provider_id']}\n"
        f"Amount:        ${claim['claim_amount']}\n"
        f"Service Date:  {claim['service_date']}\n\n"
        f"Rejection Reasons:\n"
        + "\n".join(f"  - {r}" for r in rejection_reasons)
        + f"\n\nProcessed at: {datetime.now(timezone.utc).isoformat()}"
    )

    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"CloudClaim Rejection Alert — {claim['claim_id']}",
        Message=message
    )

    logger.info(f"Rejection alert published for claim {claim['claim_id']}")


def write_to_dynamodb(claim: dict, status: str,
                      rejection_reasons: list = None):
    """Write claim result to DynamoDB."""
    table = dynamodb.Table(TABLE_NAME)

    item = {
        'claim_id': claim['claim_id'],
        'patient_id': claim['patient_id'],
        'provider_id': claim['provider_id'],
        'procedure_code': claim['procedure_code'],
        'diagnosis_code': claim['diagnosis_code'],
        'claim_amount': str(claim['claim_amount']),
        'service_date': claim['service_date'],
        'status': status,
        'processed_at': datetime.now(timezone.utc).isoformat()
    }

    if rejection_reasons:
        item['rejection_reasons'] = rejection_reasons

    table.put_item(Item=item)
    return item


def handler(event, context):
    """
    Rules engine Lambda entry point.
    Triggered by SQS — processes one batch of claim messages.
    """
    logger.info(
        f"Rules engine invoked with "
        f"{len(event.get('Records', []))} messages"
    )

    for record in event.get('Records', []):
        try:
            claim = json.loads(record['body'])
            claim_id = claim.get('claim_id', 'UNKNOWN')

            logger.info(f"Applying business rules to claim {claim_id}")

            is_approved, rejection_reasons = apply_business_rules(claim)

            if is_approved:
                write_to_dynamodb(claim, 'APPROVED')
                logger.info(f"Claim {claim_id} APPROVED")
            else:
                write_to_dynamodb(claim, 'REJECTED', rejection_reasons)
                publish_rejection_alert(claim, rejection_reasons)
                logger.warning(
                    f"Claim {claim_id} REJECTED — "
                    f"reasons: {rejection_reasons}"
                )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    return {
        'statusCode': 200,
        'body': json.dumps('Rules engine processing complete')
    }
    