import json


def lambda_handler(event, context):
    response = {
        "message": "CloudClaim ingestion lambda is working",
        "status": "success"
    }

    return {
        "statusCode": 200,
        "body": json.dumps(response)
    }