import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'cloudclaim-claims')


def build_response(status_code: int, body: dict) -> dict:
    """Build a properly formatted API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }


def handler(event, context):
    """
    Query Lambda entry point.
    Triggered by API Gateway GET /claims/{claim_id}
    Returns claim details from DynamoDB.
    """
    logger.info(f"Query Lambda invoked: {json.dumps(event)}")

    try:
        path_params = event.get('pathParameters') or {}
        claim_id = path_params.get('claim_id')

        if not claim_id:
            return build_response(400, {
                'error': 'Missing claim_id in request path',
                'message': 'Use GET /claims/{claim_id}'
            })

        logger.info(f"Querying DynamoDB for claim: {claim_id}")

        table = dynamodb.Table(TABLE_NAME)
        result = table.get_item(
            Key={'claim_id': claim_id}
        )

        item = result.get('Item')

        if not item:
            return build_response(404, {
                'error': 'Claim not found',
                'claim_id': claim_id
            })

        logger.info(f"Found claim {claim_id} with status {item['status']}")

        return build_response(200, {
            'claim_id': item['claim_id'],
            'patient_id': item['patient_id'],
            'provider_id': item['provider_id'],
            'procedure_code': item['procedure_code'],
            'diagnosis_code': item['diagnosis_code'],
            'claim_amount': item['claim_amount'],
            'service_date': item['service_date'],
            'status': item['status'],
            'processed_at': item['processed_at'],
            'rejection_reasons': item.get('rejection_reasons', [])
        })

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return build_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })