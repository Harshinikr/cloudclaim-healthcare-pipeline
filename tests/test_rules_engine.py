import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                '..', 'lambda', 'rules_engine'))

from handler import apply_business_rules


# ── Valid claim ────────────────────────────────────────────────
def test_valid_claim_is_approved():
    claim = {
        'claim_id': 'CLM-TEST-001',
        'patient_id': 'PAT-111',
        'provider_id': 'PRV-222',
        'procedure_code': '99213',
        'diagnosis_code': 'J06.9',
        'claim_amount': 250.00,
        'service_date': '2026-01-15'
    }
    is_approved, reasons = apply_business_rules(claim)
    assert is_approved is True
    assert reasons == []


# ── Amount rules ───────────────────────────────────────────────
def test_claim_amount_exceeds_maximum():
    claim = {
        'claim_id': 'CLM-TEST-002',
        'patient_id': 'PAT-111',
        'provider_id': 'PRV-222',
        'procedure_code': '99213',
        'diagnosis_code': 'J06.9',
        'claim_amount': 75000.00,
        'service_date': '2026-01-15'
    }
    is_approved, reasons = apply_business_rules(claim)
    assert is_approved is False
    assert any('exceeds maximum' in r for r in reasons)


def test_claim_amount_zero_is_rejected():
    claim = {
        'claim_id': 'CLM-TEST-003',
        'patient_id': 'PAT-111',
        'provider_id': 'PRV-222',
        'procedure_code': '99213',
        'diagnosis_code': 'J06.9',
        'claim_amount': 0,
        'service_date': '2026-01-15'
    }
    is_approved, reasons = apply_business_rules(claim)
    assert is_approved is False
    assert any('greater than $0' in r for r in reasons)


# ── Procedure code rules ───────────────────────────────────────
def test_invalid_procedure_code_rejected():
    claim = {
        'claim_id': 'CLM-TEST-004',
        'patient_id': 'PAT-111',
        'provider_id': 'PRV-222',
        'procedure_code': 'INVALID',
        'diagnosis_code': 'J06.9',
        'claim_amount': 250.00,
        'service_date': '2026-01-15'
    }
    is_approved, reasons = apply_business_rules(claim)
    assert is_approved is False
    assert any('CPT format' in r for r in reasons)


def test_valid_procedure_code_passes():
    claim = {
        'claim_id': 'CLM-TEST-005',
        'patient_id': 'PAT-111',
        'provider_id': 'PRV-222',
        'procedure_code': '99214',
        'diagnosis_code': 'J06.9',
        'claim_amount': 250.00,
        'service_date': '2026-01-15'
    }
    is_approved, reasons = apply_business_rules(claim)
    assert is_approved is True


# ── Diagnosis code rules ───────────────────────────────────────
def test_invalid_diagnosis_code_rejected():
    claim = {
        'claim_id': 'CLM-TEST-006',
        'patient_id': 'PAT-111',
        'provider_id': 'PRV-222',
        'procedure_code': '99213',
        'diagnosis_code': 'INVALID',
        'claim_amount': 250.00,
        'service_date': '2026-01-15'
    }
    is_approved, reasons = apply_business_rules(claim)
    assert is_approved is False
    assert any('ICD-10' in r for r in reasons)


# ── Date rules ─────────────────────────────────────────────────
def test_future_service_date_rejected():
    claim = {
        'claim_id': 'CLM-TEST-007',
        'patient_id': 'PAT-111',
        'provider_id': 'PRV-222',
        'procedure_code': '99213',
        'diagnosis_code': 'J06.9',
        'claim_amount': 250.00,
        'service_date': '2099-01-01'
    }
    is_approved, reasons = apply_business_rules(claim)
    assert is_approved is False
    assert any('future' in r for r in reasons)


# ── Multiple failures ──────────────────────────────────────────
def test_multiple_violations_all_reported():
    claim = {
        'claim_id': 'CLM-TEST-008',
        'patient_id': 'PAT-111',
        'provider_id': 'PRV-222',
        'procedure_code': 'BAD',
        'diagnosis_code': 'INVALID',
        'claim_amount': 99999.00,
        'service_date': '2026-01-15'
    }
    is_approved, reasons = apply_business_rules(claim)
    assert is_approved is False
    assert len(reasons) >= 3