import uuid

import pytest
from fastapi.testclient import TestClient

"""
Tests for account handler endpoints.
These tests use the fixtures and test data setup in conftest.py.
"""


def test_get_all_accounts(client: TestClient):
    """Test retrieving all accounts."""
    response = client.get("/accounts")

    assert response.status_code == 200
    accounts = response.json()

    # Verify all 4 seeded accounts are returned
    assert len(accounts) == 4

    # Verify account data includes expected account IDs
    account_ids = [account["id"] for account in accounts]
    assert str(pytest.ACCOUNT_ID_1) in account_ids
    assert str(pytest.ACCOUNT_ID_2) in account_ids
    assert str(pytest.ACCOUNT_ID_3) in account_ids
    assert str(pytest.ACCOUNT_ID_4) in account_ids


def test_get_account_balance(client: TestClient):
    """Test retrieving account balance."""
    response = client.get(f"/accounts/{pytest.ACCOUNT_ID_1}")

    assert response.status_code == 200
    balance_data = response.json()

    # Verify the balance data is correct
    assert balance_data["id"] == str(pytest.ACCOUNT_ID_1)
    assert balance_data["customer_id"] == str(pytest.CUSTOMER_ID_1)
    assert balance_data["current_balance"] == 1000.0


def test_get_account_balance_not_found(client: TestClient):
    """Test retrieving balance for non-existent account."""
    non_existent_id = uuid.uuid4()
    response = client.get(f"/accounts/{non_existent_id}")

    assert response.status_code == 404
    assert "Account not found" in response.json()["detail"]


def test_create_account_success(client: TestClient):
    """Test successful account creation."""
    request_data = {"customer_id": str(pytest.CUSTOMER_ID_4), "initial_deposit": 750.50}

    response = client.post("/accounts", json=request_data)

    assert response.status_code == 201
    account_data = response.json()

    # Verify the created account data
    assert account_data["customer_id"] == str(pytest.CUSTOMER_ID_4)
    assert account_data["status"] == "ACTIVE"
    assert "account_number" in account_data

    # Get the account balance to verify initial deposit
    account_id = account_data["id"]
    balance_response = client.get(f"/accounts/{account_id}")

    assert balance_response.status_code == 200
    balance_data = balance_response.json()
    assert balance_data["current_balance"] == 750.50


def test_create_account_invalid_customer(client: TestClient):
    """Test account creation with non-existent customer."""
    non_existent_id = uuid.uuid4()
    request_data = {"customer_id": str(non_existent_id), "initial_deposit": 100.0}

    response = client.post("/accounts", json=request_data)

    assert response.status_code == 404
    assert "Customer not found" in response.json()["detail"]


def test_create_account_negative_deposit(client: TestClient):
    """Test account creation with negative initial deposit."""
    request_data = {"customer_id": str(pytest.CUSTOMER_ID_1), "initial_deposit": -50.0}

    response = client.post("/accounts", json=request_data)

    assert response.status_code == 400
    assert "Initial deposit cannot be negative" in response.json()["detail"]


def test_create_zero_balance_account(client: TestClient):
    """Test creating account with zero initial deposit."""
    request_data = {"customer_id": str(pytest.CUSTOMER_ID_3), "initial_deposit": 0.0}

    response = client.post("/accounts", json=request_data)

    assert response.status_code == 201
    account_data = response.json()

    # Get the account balance to verify zero balance
    account_id = account_data["id"]
    balance_response = client.get(f"/accounts/{account_id}")

    assert balance_response.status_code == 200
    balance_data = balance_response.json()
    assert balance_data["current_balance"] == 0.0


def test_multiple_accounts_per_customer(client: TestClient):
    """Test that a customer can have multiple accounts."""
    # Customer 1 already has 2 accounts in seed data
    # Create another account for customer 1
    request_data = {"customer_id": str(pytest.CUSTOMER_ID_1), "initial_deposit": 300.0}

    response = client.post("/accounts", json=request_data)
    assert response.status_code == 201

    # Get all accounts and filter by customer 1
    all_accounts_response = client.get("/accounts")
    accounts = all_accounts_response.json()
    customer1_accounts = [a for a in accounts if a["customer_id"] == str(pytest.CUSTOMER_ID_1)]

    # Verify customer now has 3 accounts
    assert len(customer1_accounts) == 3
