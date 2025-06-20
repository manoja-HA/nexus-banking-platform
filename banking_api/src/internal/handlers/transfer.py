from uuid import UUID

from fastapi import APIRouter, Depends, status
from internal.dependencies.transfer import get_transfer_service
from internal.models.transfer import CreateTransferRequest, TransferDetailsResponse
from internal.service.transfer import TransferService

router: APIRouter = APIRouter()


@router.post("/transfers", response_model=TransferDetailsResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    request: CreateTransferRequest, transfer_service: TransferService = Depends(get_transfer_service)
) -> TransferDetailsResponse:
    """Transfer funds between two accounts.

    - **source_account_id**: ID of the source account
    - **destination_account_id**: ID of the destination account
    - **amount**: Amount to transfer (must be positive)
    - **idempotency_key**: Optional unique key to prevent duplicate transfers
    - **description**: Description of the transfer
    - **transfer_type**: Type of transfer (DEBIT, CREDIT)

    Returns the transfer details.
    """
    return transfer_service.create_transfer(request)


@router.get("/transfers/{account_id}/history", response_model=list[TransferDetailsResponse])
async def get_account_transfer_history(
    account_id: UUID, transfer_service: TransferService = Depends(get_transfer_service)
) -> list[TransferDetailsResponse]:
    """Get transfer history for a specific account.

    - **account_id**: ID of the account

    Returns a list of transfers where the account is either source or destination.
    """
    return transfer_service.get_account_transfer_history(account_id)
