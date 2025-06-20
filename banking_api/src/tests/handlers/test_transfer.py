import uuid

import pytest
from fastapi.testclient import TestClient

"""
Tests for transfer handler endpoints.
These tests use the fixtures and test data setup in conftest.py.
"""


def test_create_transfer_success(client: TestClient):
    """Test successful money transfer between active accounts."""
    # Initial balances from seed data
    initial_source_balance = 1000.0  # ACCOUNT_ID_1
    initial_dest_balance = 500.0  # ACCOUNT_ID_2
    transfer_amount = 200.0

    # Create transfer request
    transfer_request = {
        "source_account_id": str(pytest.ACCOUNT_ID_1),
        "destination_account_id": str(pytest.ACCOUNT_ID_2),
        "amount": transfer_amount,
        "description": "Test transfer",
        "idempotency_key": str(uuid.uuid4()),
    }

    # Execute transfer
    response = client.post("/transfers", json=transfer_request)

    # Verify response
    assert response.status_code == 201
    transfer_data = response.json()
    assert transfer_data["source_account_id"] == str(pytest.ACCOUNT_ID_1)
    assert transfer_data["destination_account_id"] == str(pytest.ACCOUNT_ID_2)
    assert transfer_data["amount"] == transfer_amount
    assert transfer_data["status"] == "COMPLETED"

    # Verify source account balance updated correctly
    source_balance_response = client.get(f"/accounts/{pytest.ACCOUNT_ID_1}")
    assert source_balance_response.status_code == 200
    source_balance_data = source_balance_response.json()
    assert source_balance_data["current_balance"] == initial_source_balance - transfer_amount

    # Verify destination account balance updated correctly
    dest_balance_response = client.get(f"/accounts/{pytest.ACCOUNT_ID_2}")
    assert dest_balance_response.status_code == 200
    dest_balance_data = dest_balance_response.json()
    assert dest_balance_data["current_balance"] == initial_dest_balance + transfer_amount


def test_transfer_insufficient_funds(client: TestClient):
    """Test transfer with insufficient funds in source account."""
    # Account 3 has 250.0 balance in seed data
    transfer_amount = 500.0  # More than available

    # Create transfer request
    transfer_request = {
        "source_account_id": str(pytest.ACCOUNT_ID_3),
        "destination_account_id": str(pytest.ACCOUNT_ID_2),
        "amount": transfer_amount,
        "description": "Test insufficient funds transfer",
        "idempotency_key": str(uuid.uuid4()),
    }

    # Execute transfer
    response = client.post("/transfers", json=transfer_request)

    # Verify response indicates insufficient funds
    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


def test_transfer_to_inactive_account(client: TestClient):
    """Test transfer to an inactive account."""
    # Account 4 is inactive in seed data
    transfer_request = {
        "source_account_id": str(pytest.ACCOUNT_ID_1),
        "destination_account_id": str(pytest.ACCOUNT_ID_4),
        "amount": 50.0,
        "description": "Test transfer to inactive account",
        "idempotency_key": str(uuid.uuid4()),
    }

    # Execute transfer
    response = client.post("/transfers", json=transfer_request)

    # Verify response indicates account inactive
    assert response.status_code == 400
    assert "is not active" in response.json()["detail"]


def test_transfer_from_inactive_account(client: TestClient):
    """Test transfer from an inactive account."""
    # Account 4 is inactive in seed data
    transfer_request = {
        "source_account_id": str(pytest.ACCOUNT_ID_4),
        "destination_account_id": str(pytest.ACCOUNT_ID_1),
        "amount": 50.0,
        "description": "Test transfer from inactive account",
        "idempotency_key": str(uuid.uuid4()),
    }

    # Execute transfer
    response = client.post("/transfers", json=transfer_request)

    # Verify response indicates account inactive
    assert response.status_code == 400
    assert "is not active" in response.json()["detail"]


def test_transfer_idempotency(client: TestClient):
    """Test idempotency for transfers (same request should not execute twice)."""
    # Initial balances
    initial_source_balance = 1000.0  # ACCOUNT_ID_1
    initial_dest_balance = 500.0  # ACCOUNT_ID_2
    transfer_amount = 150.0

    # Create idempotency key for both requests
    idempotency_key = str(uuid.uuid4())

    # Create transfer request
    transfer_request = {
        "source_account_id": str(pytest.ACCOUNT_ID_1),
        "destination_account_id": str(pytest.ACCOUNT_ID_2),
        "amount": transfer_amount,
        "description": "Test idempotent transfer",
        "idempotency_key": idempotency_key,
    }

    # Execute first transfer
    response1 = client.post("/transfers", json=transfer_request)
    assert response1.status_code == 201
    transfer_id1 = response1.json()["id"]

    # Execute second transfer with same idempotency key
    response2 = client.post("/transfers", json=transfer_request)
    assert response2.status_code == 201
    transfer_id2 = response2.json()["id"]

    # Both responses should contain same transfer ID
    assert transfer_id1 == transfer_id2

    # Verify balances were only updated once
    source_balance_response = client.get(f"/accounts/{pytest.ACCOUNT_ID_1}")
    assert source_balance_response.status_code == 200
    source_balance_data = source_balance_response.json()
    assert source_balance_data["current_balance"] == initial_source_balance - transfer_amount

    dest_balance_response = client.get(f"/accounts/{pytest.ACCOUNT_ID_2}")
    assert dest_balance_response.status_code == 200
    dest_balance_data = dest_balance_response.json()
    assert dest_balance_data["current_balance"] == initial_dest_balance + transfer_amount


def test_transfer_zero_amount(client: TestClient):
    """Test transfer with zero amount."""
    transfer_request = {
        "source_account_id": str(pytest.ACCOUNT_ID_1),
        "destination_account_id": str(pytest.ACCOUNT_ID_2),
        "amount": 0.0,
        "description": "Test zero amount transfer",
        "idempotency_key": str(uuid.uuid4()),
    }

    response = client.post("/transfers", json=transfer_request)

    # Should fail validation
    assert response.status_code == 400
    assert "Transfer amount must be positive" in response.json()["detail"]


def test_transfer_negative_amount(client: TestClient):
    """Test transfer with negative amount."""
    transfer_request = {
        "source_account_id": str(pytest.ACCOUNT_ID_1),
        "destination_account_id": str(pytest.ACCOUNT_ID_2),
        "amount": -50.0,
        "description": "Test negative amount transfer",
        "idempotency_key": str(uuid.uuid4()),
    }

    response = client.post("/transfers", json=transfer_request)

    # Should fail validation
    assert response.status_code == 400
    assert "Transfer amount must be positive" in response.json()["detail"]


def test_transfer_to_self(client: TestClient):
    """Test transfer to same account (should be disallowed for standard transfers)."""
    transfer_request = {
        "source_account_id": str(pytest.ACCOUNT_ID_1),
        "destination_account_id": str(pytest.ACCOUNT_ID_1),
        "amount": 50.0,
        "description": "Test transfer to self",
        "idempotency_key": str(uuid.uuid4()),
    }

    response = client.post("/transfers", json=transfer_request)

    # Should be disallowed
    assert response.status_code == 400
    assert "Source and destination accounts cannot be the same" in response.json()["detail"]


def test_get_account_transfer_history(client: TestClient):
    """Test retrieving transfer history for an account."""
    # Account 2 has both incoming and outgoing transfers in seed data
    response = client.get(f"/transfers/{pytest.ACCOUNT_ID_2}/history")

    assert response.status_code == 200
    transfers = response.json()

    # Verify at least 2 transfers are returned (from seed data)
    assert len(transfers) >= 2

    # Verify the expected transfer IDs are in the results
    transfer_ids = [transfer["id"] for transfer in transfers]
    assert str(pytest.TRANSFER_ID_1) in transfer_ids
    assert str(pytest.TRANSFER_ID_2) in transfer_ids

    # Verify one transfer has Account 2 as destination and one as source
    source_transfers = [t for t in transfers if t["source_account_id"] == str(pytest.ACCOUNT_ID_2)]
    dest_transfers = [t for t in transfers if t["destination_account_id"] == str(pytest.ACCOUNT_ID_2)]

    assert len(source_transfers) >= 1
    assert len(dest_transfers) >= 1
