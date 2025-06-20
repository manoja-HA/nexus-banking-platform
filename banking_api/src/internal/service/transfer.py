from decimal import Decimal
from typing import Self
from uuid import UUID

from fastapi import HTTPException, status
from internal.helpers.app_exceptions import AppError
from internal.helpers.utils import get_uuid
from internal.models.account import AccountDB, AccountStatus
from internal.models.transfer import (
    CreateTransferRequest,
    TransferDB,
    TransferDetailsResponse,
    TransferStatus,
    TransferType,
)
from internal.repos.account import AccountRepo
from internal.repos.transfer import TransferRepo


class TransferService:
    def __init__(self: Self, account_repo: AccountRepo, transfer_repo: TransferRepo) -> None:
        self.account_repo = account_repo
        self.transfer_repo = transfer_repo

    def create_transfer(self: Self, request: CreateTransferRequest) -> TransferDetailsResponse:
        """Transfer funds between two accounts.

        Args:
            request: Contains source and destination account IDs, amount, and metadata

        Returns:
            TransferDetailsResponse with transfer details

        Raises:
            HTTPException: If validation fails or processing error occurs
        """
        # Validate request data
        self._validate_transfer_request(request)

        # Check for duplicate transfer using idempotency key
        existing_transfer = self.transfer_repo.get_transfer_by_idempotency_key(request.idempotency_key)
        if existing_transfer:
            # TODO: If the transfer exists and is in PENDING state (likely due to an interrupted transaction),
            # attempt to recover and complete the pending transfer to ensure consistency.

            return TransferDetailsResponse.model_validate(existing_transfer)

        try:
            with self.transfer_repo.transaction():
                # Get accounts and validate their status
                source_account = self.account_repo.get_account(request.source_account_id)
                destination_account = self.account_repo.get_account(request.destination_account_id)

                # TODO: Validate that the source and destination accounts are not the same
                self._validate_account_status(source_account)
                self._validate_account_status(destination_account)
                # Check sufficient funds (except for initial deposits)
                if (
                    source_account.current_balance < request.amount
                    and request.transfer_type != TransferType.INITIAL_DEPOSIT
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient funds in source account. Available: {source_account.current_balance}, Requested: {request.amount}",
                    )

                # Create pending transfer record first
                transfer = TransferDB(
                    id=get_uuid(),
                    source_account_id=request.source_account_id,
                    destination_account_id=request.destination_account_id,
                    amount=request.amount,
                    transfer_type=request.transfer_type,
                    status=TransferStatus.PENDING,
                    idempotency_key=request.idempotency_key,
                    description=request.description,
                )

                transfer = self.transfer_repo.create_transfer(transfer)

                # Update account balances
                if request.transfer_type != TransferType.INITIAL_DEPOSIT:
                    new_source_balance = source_account.current_balance - request.amount
                    source_account = self.account_repo.update_account_balance(source_account.id, new_source_balance)

                new_destination_balance = destination_account.current_balance + request.amount
                destination_account = self.account_repo.update_account_balance(
                    destination_account.id, new_destination_balance
                )

                # Mark transfer as completed
                transfer = self.transfer_repo.update_transfer_status(transfer.id, TransferStatus.COMPLETED)

                return TransferDetailsResponse.model_validate(transfer)

        except HTTPException:
            # Let HTTP exceptions propagate
            raise
        except AppError as e:
            # Let application errors propagate with their status codes
            raise HTTPException(status_code=e.status_code, detail=e.detail)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing the transfer. Please try again later.",
            )

    def get_account_transfer_history(self: Self, account_id: UUID) -> list[TransferDetailsResponse]:
        """Get transfer history for a specific account.

        Args:
            account_id: UUID of the account

        Returns:
            List of TransferDetailsResponse objects

        Raises:
            HTTPException: If account not found or processing error occurs
        """
        try:
            # Verify account exists
            self.account_repo.get_account(account_id)

            # Get transfers
            transfers = self.transfer_repo.get_account_transfers(account_id)

            # Map to response models
            transfer_responses: list[TransferDetailsResponse] = []
            for transfer in transfers:
                transfer_responses.append(TransferDetailsResponse.model_validate(transfer))

            return transfer_responses

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get transfer history: {e!s}"
            )

    def get_transfer(self: Self, transfer_id: UUID) -> TransferDetailsResponse:
        """Get details of a specific transfer.

        Args:
            transfer_id: UUID of the transfer

        Returns:
            TransferDetailsResponse with transfer details

        Raises:
            HTTPException: If transfer not found
        """
        try:
            transfer = self.transfer_repo.get_transfer(transfer_id)
            return TransferDetailsResponse.model_validate(transfer)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get transfer: {e!s}"
            )

    def _validate_account_status(self, account: AccountDB) -> None:
        """Validate that an account is active.

        Args:
            account: The account to validate

        Raises:
            HTTPException: If account is not active
        """
        if account.status != AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Account with ID:{account.id} is not active"
            )

    def _validate_transfer_request(self, request: CreateTransferRequest) -> None:
        """Validate a transfer request.

        Args:
            request: The transfer request to validate

        Raises:
            HTTPException: If validation fails
        """
        if request.amount <= Decimal("0"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer amount must be positive")

        if (
            request.source_account_id == request.destination_account_id
            and request.transfer_type != TransferType.INITIAL_DEPOSIT
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Source and destination accounts cannot be the same"
            )
