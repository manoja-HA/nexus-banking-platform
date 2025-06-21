from uuid import UUID

from fastapi import APIRouter, Depends, status
from internal.dependencies.account import get_account_service
from internal.models.account import AccountBalanceResponse, AccountDetailsResponse, CreateAccountRequest
from internal.service.account import AccountService

router: APIRouter = APIRouter()


@router.post("/accounts", response_model=AccountDetailsResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    request: CreateAccountRequest, account_service: AccountService = Depends(get_account_service)
) -> AccountDetailsResponse:
    """Create a new bank account for a customer with an initial deposit.

    - **customer_id**: ID of the existing customer
    - **initial_deposit**: Amount to deposit initially (must be positive or zero)

    Returns the newly created account details.
    """
    return account_service.create_account(request)


@router.get("/accounts", response_model=list[AccountDetailsResponse])
def get_all_accounts(account_service: AccountService = Depends(get_account_service)) -> list[AccountDetailsResponse]:
    """Get a list of all accounts.

    Returns a list of account details.
    """
    return account_service.get_all_accounts()


@router.get("/accounts/{account_id}", response_model=AccountBalanceResponse)
def get_account_balance(
    account_id: UUID, account_service: AccountService = Depends(get_account_service)
) -> AccountBalanceResponse:
    """Get the current balance and details for a specific account.

    - **account_id**: ID of the account to retrieve

    Returns account details including the current balance.
    """
    return account_service.get_account_balance(account_id)
