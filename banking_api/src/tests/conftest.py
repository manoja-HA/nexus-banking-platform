import os
import sys
import uuid
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add src directory to Python path to make internal imports work
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from internal.database.postgresql import get_session
from internal.dependencies.account import get_account_service
from internal.dependencies.customer import get_customer_service
from internal.dependencies.transfer import get_transfer_service
from internal.handlers.account import router as account_router
from internal.handlers.customer import router as customer_router
from internal.handlers.transfer import router as transfer_router
from internal.models.account import AccountDB, AccountStatus
from internal.models.customer import CustomerDB
from internal.models.db_base import Base
from internal.models.transfer import TransferDB, TransferStatus, TransferType
from internal.repos.account import AccountRepo
from internal.repos.customer import CustomerRepo
from internal.repos.transfer import TransferRepo
from internal.service.account import AccountService
from internal.service.customer import CustomerService
from internal.service.transfer import TransferService

# Define constant test IDs for consistent test data
CUSTOMER_ID_1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
CUSTOMER_ID_2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
CUSTOMER_ID_3 = uuid.UUID("00000000-0000-0000-0000-000000000003")
CUSTOMER_ID_4 = uuid.UUID("00000000-0000-0000-0000-000000000004")

ACCOUNT_ID_1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
ACCOUNT_ID_2 = uuid.UUID("22222222-2222-2222-2222-222222222222")
ACCOUNT_ID_3 = uuid.UUID("33333333-3333-3333-3333-333333333333")
ACCOUNT_ID_4 = uuid.UUID("44444444-4444-4444-4444-444444444444")

TRANSFER_ID_1 = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TRANSFER_ID_2 = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

# Create a test database in memory
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with appropriate settings for SQLite in-memory DB
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)


# Create all tables in the test database
@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Fixture to get a clean database session for each test
@pytest.fixture(scope="function")
def db_session(setup_database) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# Fixture to seed the database with test data
@pytest.fixture(scope="function")
def seed_database(db_session: Session) -> Session:
    # Create test customers (from the assignment)
    customers = [
        CustomerDB(id=CUSTOMER_ID_1, name="Arisha Barron", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        CustomerDB(id=CUSTOMER_ID_2, name="Branden Gibson", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        CustomerDB(id=CUSTOMER_ID_3, name="Rhonda Church", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        CustomerDB(id=CUSTOMER_ID_4, name="Georgina Hazel", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
    ]

    # Create test accounts with various balances and statuses
    accounts = [
        AccountDB(
            id=ACCOUNT_ID_1,
            customer_id=CUSTOMER_ID_1,
            account_number="DE-2025-AAAA-BBBB",
            current_balance=1000.0,
            version=1,
            status=AccountStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        AccountDB(
            id=ACCOUNT_ID_2,
            customer_id=CUSTOMER_ID_2,
            account_number="DE-2025-CCCC-DDDD",
            current_balance=500.0,
            version=1,
            status=AccountStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        AccountDB(
            id=ACCOUNT_ID_3,
            customer_id=CUSTOMER_ID_1,
            account_number="DE-2025-EEEE-FFFF",
            current_balance=250.0,
            version=1,
            status=AccountStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        AccountDB(
            id=ACCOUNT_ID_4,
            customer_id=CUSTOMER_ID_3,
            account_number="DE-2025-GGGG-HHHH",
            current_balance=0.0,
            version=1,
            status=AccountStatus.INACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]

    # Create some test transfers between accounts
    transfers = [
        TransferDB(
            id=TRANSFER_ID_1,
            source_account_id=ACCOUNT_ID_1,
            destination_account_id=ACCOUNT_ID_2,
            amount=100.0,
            status=TransferStatus.COMPLETED,
            description="Initial test transfer",
            transfer_type=TransferType.STANDARD,
            idempotency_key=uuid.uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            is_initial_deposit=False,
        ),
        TransferDB(
            id=TRANSFER_ID_2,
            source_account_id=ACCOUNT_ID_2,
            destination_account_id=ACCOUNT_ID_3,
            amount=50.0,
            status=TransferStatus.COMPLETED,
            description="Second test transfer",
            transfer_type=TransferType.STANDARD,
            idempotency_key=uuid.uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            is_initial_deposit=False,
        ),
    ]

    # Add all test data to the session
    db_session.add_all(customers)
    db_session.add_all(accounts)
    db_session.add_all(transfers)

    # Commit the changes
    db_session.commit()

    return db_session


# Fixture to create a FastAPI test client with all dependencies overridden
@pytest.fixture(scope="function")
def client(seed_database) -> TestClient:
    app = FastAPI()

    # Add all routers to the app
    app.include_router(account_router)
    app.include_router(transfer_router)
    app.include_router(customer_router)

    # Use the seeded database session
    db_session = seed_database

    # Create repositories
    customer_repo = CustomerRepo(session=db_session)
    account_repo = AccountRepo(session=db_session)
    transfer_repo = TransferRepo(session=db_session)

    # Create services with the repositories
    account_service = AccountService(
        session=db_session, customer_repo=customer_repo, account_repo=account_repo, transfer_repo=transfer_repo
    )

    customer_service = CustomerService(customer_repo=customer_repo)

    transfer_service = TransferService(account_repo=account_repo, transfer_repo=transfer_repo)

    # Override all dependencies
    def override_get_session():
        try:
            yield db_session
        finally:
            pass

    def override_get_account_service():
        return account_service

    def override_get_customer_service():
        return customer_service

    def override_get_transfer_service():
        return transfer_service

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_account_service] = override_get_account_service
    app.dependency_overrides[get_customer_service] = override_get_customer_service
    app.dependency_overrides[get_transfer_service] = override_get_transfer_service

    return TestClient(app)


# Expose test constants to be imported in test modules
def pytest_configure(config):
    """Add test constants to pytest namespace for easy importing in test files."""
    pytest.CUSTOMER_ID_1 = CUSTOMER_ID_1
    pytest.CUSTOMER_ID_2 = CUSTOMER_ID_2
    pytest.CUSTOMER_ID_3 = CUSTOMER_ID_3
    pytest.CUSTOMER_ID_4 = CUSTOMER_ID_4

    pytest.ACCOUNT_ID_1 = ACCOUNT_ID_1
    pytest.ACCOUNT_ID_2 = ACCOUNT_ID_2
    pytest.ACCOUNT_ID_3 = ACCOUNT_ID_3
    pytest.ACCOUNT_ID_4 = ACCOUNT_ID_4

    pytest.TRANSFER_ID_1 = TRANSFER_ID_1
    pytest.TRANSFER_ID_2 = TRANSFER_ID_2
