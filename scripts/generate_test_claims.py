import json
import random
import boto3
import time
from datetime import datetime, timedelta

# Real CPT codes (office visits, common procedures)
VALID_CPT_CODES = [
    "99201", "99202", "99203", "99204", "99205",
    "99211", "99212", "99213", "99214", "99215",
    "93000", "71046", "80053", "85025", "36415",
    "99232", "99233", "99238", "99239", "99291"
]

INVALID_CPT_CODES = ["INVALID", "ABC12", "9921", "992131", "XXXXX"]

# Real ICD-10 codes (common diagnoses)
VALID_ICD10_CODES = [
    "J06.9", "J18.9", "I10", "E11.9", "M54.5",
    "Z00.00", "J20.9", "N39.0", "K21.0", "F32.9",
    "Z12.11", "I25.10", "E78.5", "M17.11", "G43.909"
]

INVALID_ICD10_CODES = ["INVALID", "123", "ZZZ", "AB", "12345"]

s3_client = boto3.client('s3', region_name='us-east-1')
BUCKET = 'cloudclaim-harsh-dev-2026'


def random_date_in_past(max_days_ago=365):
    days_ago = random.randint(1, max_days_ago)
    return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')


def random_future_date():
    days_ahead = random.randint(1, 90)
    return (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')


def generate_claim(index, force_invalid=False):
    """Generate a single claim — mostly valid, some intentionally invalid."""

    claim_id = f"CLM-BULK-{index:05d}"
    patient_id = f"PAT-{random.randint(10000, 99999)}"
    provider_id = f"PRV-{random.randint(10000, 99999)}"

    # 80% valid claims, 20% invalid across various rules
    roll = random.random()

    if force_invalid or roll > 0.80:
        # Generate an invalid claim — pick one failure mode
        failure = random.choice([
            'bad_amount_high',
            'bad_amount_zero',
            'bad_cpt',
            'bad_icd10',
            'future_date'
        ])

        if failure == 'bad_amount_high':
            return {
                "claim_id": claim_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "procedure_code": random.choice(VALID_CPT_CODES),
                "diagnosis_code": random.choice(VALID_ICD10_CODES),
                "claim_amount": round(random.uniform(50001, 200000), 2),
                "service_date": random_date_in_past()
            }
        elif failure == 'bad_amount_zero':
            return {
                "claim_id": claim_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "procedure_code": random.choice(VALID_CPT_CODES),
                "diagnosis_code": random.choice(VALID_ICD10_CODES),
                "claim_amount": 0,
                "service_date": random_date_in_past()
            }
        elif failure == 'bad_cpt':
            return {
                "claim_id": claim_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "procedure_code": random.choice(INVALID_CPT_CODES),
                "diagnosis_code": random.choice(VALID_ICD10_CODES),
                "claim_amount": round(random.uniform(50, 5000), 2),
                "service_date": random_date_in_past()
            }
        elif failure == 'bad_icd10':
            return {
                "claim_id": claim_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "procedure_code": random.choice(VALID_CPT_CODES),
                "diagnosis_code": random.choice(INVALID_ICD10_CODES),
                "claim_amount": round(random.uniform(50, 5000), 2),
                "service_date": random_date_in_past()
            }
        else:  # future_date
            return {
                "claim_id": claim_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "procedure_code": random.choice(VALID_CPT_CODES),
                "diagnosis_code": random.choice(VALID_ICD10_CODES),
                "claim_amount": round(random.uniform(50, 5000), 2),
                "service_date": random_future_date()
            }
    else:
        # Valid claim
        return {
            "claim_id": claim_id,
            "patient_id": patient_id,
            "provider_id": provider_id,
            "procedure_code": random.choice(VALID_CPT_CODES),
            "diagnosis_code": random.choice(VALID_ICD10_CODES),
            "claim_amount": round(random.uniform(50, 49999), 2),
            "service_date": random_date_in_past()
        }


def upload_claim(claim):
    """Upload a single claim JSON to S3."""
    key = f"claims/bulk/{claim['claim_id']}.json"
    s3_client.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=json.dumps(claim),
        ContentType='application/json'
    )


def main():
    total = 1000
    batch_size = 50
    uploaded = 0
    failed = 0

    print(f"Generating and uploading {total} claims to S3...")
    print(f"Bucket: {BUCKET}")
    print(f"Mix: ~80% valid, ~20% invalid\n")

    for i in range(1, total + 1):
        try:
            claim = generate_claim(i)
            upload_claim(claim)
            uploaded += 1

            if uploaded % batch_size == 0:
                print(f"Uploaded {uploaded}/{total} claims...")
                # Small pause every 50 uploads to avoid overwhelming Lambda
                time.sleep(2)

        except Exception as e:
            print(f"Failed to upload claim {i}: {str(e)}")
            failed += 1

    print(f"\nDone.")
    print(f"Successfully uploaded: {uploaded}")
    print(f"Failed: {failed}")
    print(f"Check DynamoDB table 'cloudclaim-claims' for results.")


if __name__ == "__main__":
    main()