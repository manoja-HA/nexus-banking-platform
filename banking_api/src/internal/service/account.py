from typing import Self
from uuid import UUID

from fastapi import HTTPException, status
from internal.helpers.utils import generate_unique_account_number, get_uuid
from internal.models.account import (
    AccountBalanceResponse,
    AccountDB,
    AccountDetailsResponse,
    AccountStatus,
    CreateAccountRequest,
)
from internal.models.transfer import TransferDB, TransferStatus, TransferType
from internal.repos.account import AccountRepo
from internal.repos.customer import CustomerRepo
from internal.repos.transfer import TransferRepo
from sqlalchemy.orm import Session


class AccountService:
    def __init__(
        self, session: Session, customer_repo: CustomerRepo, account_repo: AccountRepo, transfer_repo: TransferRepo
    ) -> None:
        self.session = session
        self.transfer_repo = transfer_repo
        self.account_repo = account_repo
        self.customer_repo = customer_repo

    def create_account(self: Self, request: CreateAccountRequest) -> AccountDetailsResponse:
        """Create a new bank account for an existing customer with an optional initial deposit.

        Args:
            request: CreateAccountRequest containing customer_id and initial_deposit

        Returns:
            AccountDetailsResponse with the newly created account details

        Raises:
            HTTPException: If customer not found or validation fails
        """
        if request.initial_deposit < 0:
            raise HTTPException(status_code=400, detail="Initial deposit cannot be negative")

        try:
            self.customer_repo.get_customer(request.customer_id)
        except HTTPException as exp:
            raise exp

        try:
            # Generate unique account number
            account_number = generate_unique_account_number()

            # Create account with zero balance initially
            account_db = AccountDB(
                id=get_uuid(),
                customer_id=request.customer_id,
                account_number=account_number,
                current_balance=0,
                version=1,
                status=AccountStatus.ACTIVE,
            )

            account = self.account_repo.create_account(account_db)

            # Process initial deposit as a separate transaction if amount > 0
            if request.initial_deposit > 0:
                transfer = TransferDB(
                    id=get_uuid(),
                    source_account_id=account.id,
                    destination_account_id=account.id,
                    amount=request.initial_deposit,
                    transfer_type=TransferType.INITIAL_DEPOSIT,
                    status=TransferStatus.COMPLETED,
                    is_initial_deposit=True,
                    idempotency_key=get_uuid(),
                    description="Initial deposit",
                )

                self.transfer_repo.create_transfer(transfer)

                # Update account balance
                account = self.account_repo.update_account_balance(
                    account.id, (account.current_balance) + (request.initial_deposit)
                )

            return AccountDetailsResponse.model_validate(account)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create account: {e!s}"
            )

    def get_account_balance(self: Self, account_id: UUID) -> AccountBalanceResponse:
        """Get current balance and details for a specific account.

        Args:
            account_id: UUID of the account

        Returns:
            AccountBalanceResponse with current balance and account details

        Raises:
            HTTPException: If account not found
        """
        try:
            account = self.account_repo.get_account(account_id)
            return AccountBalanceResponse.model_validate(account)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get account balance: {e!s}"
            )

    def get_all_accounts(self: Self) -> list[AccountDetailsResponse]:
        """Get all accounts in the system.

        Returns:
            List of AccountDetailsResponse with all account details

        Raises:
            HTTPException: If an error occurs while fetching accounts
        """
        try:
            accounts = self.account_repo.get_all_accounts()
            return [AccountDetailsResponse.model_validate(account) for account in accounts]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get all accounts: {e!s}"
            )
