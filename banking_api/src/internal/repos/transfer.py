import logging
from contextlib import contextmanager
from typing import Self
from uuid import UUID

from fastapi import status
from internal.helpers.app_exceptions import AppError, AppErrorType
from internal.helpers.utils import get_uuid
from internal.models.transfer import TransferDB, TransferStatus
from sqlalchemy import or_
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.session import Session

logger = logging.getLogger(__name__)


class TransferRepo:
    """Repository for managing transfer operations in the database.
    Handles creating, updating, and retrieving transfer records.
    """

    def __init__(self: Self, session: Session) -> None:
        """Initialize the transfer repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session: Session = session

    @contextmanager
    def transaction(self):
        """Provide a transactional context for multiple database operations.
        Automatically commits on success or rolls back on exception.

        Yields:
            The active session for use within the transaction
        """
        try:
            yield self.session
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

    def create_transfer(self: Self, item: TransferDB) -> TransferDB:
        """Create a new transfer record.

        Args:
            item: TransferDB instance with transfer details

        Returns:
            The created TransferDB instance with ID and timestamps

        Raises:
            AppError: For constraint violations
            Exception: For other database errors
        """
        try:
            if item.id is None:  # pyright: ignore
                item.id = get_uuid()

            self.session.add(item)
            self.session.commit()
            self.session.refresh(item)

            logger.info(
                f"Created transfer {item.id} from {item.source_account_id} to {item.destination_account_id} for amount {item.amount}"
            )
            return item

        except DBAPIError as e:
            self.session.rollback()
            if e.orig is not None and AppErrorType.ERROR_UNIQUE_CONSTRAINT.value in str(e.orig):
                raise AppError(
                    AppErrorType.ERROR_UNIQUE_CONSTRAINT,
                    detail="A transfer with this idempotency key already exists",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            logger.error(f"Database error creating transfer: {e}")
            raise AppError(
                AppErrorType.ERROR_DATABASE,
                detail="Failed to create transfer",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            self.session.rollback()
            logger.error(f"Unexpected error creating transfer: {e}")
            raise AppError(
                AppErrorType.ERROR_INTERNAL,
                detail="An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_transfer(self: Self, transfer_id: UUID) -> TransferDB:
        """Retrieve a specific transfer by ID.

        Args:
            transfer_id: UUID of the transfer

        Returns:
            TransferDB instance with transfer details

        Raises:
            AppError: If transfer not found
        """
        transfer: TransferDB | None = self.session.query(TransferDB).filter(TransferDB.id == transfer_id).first()

        if not transfer:
            logger.warning(f"Transfer {transfer_id} not found")
            raise AppError(
                AppErrorType.ERROR_NOT_FOUND,
                detail="Transfer not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return transfer

    def get_account_transfers(self: Self, account_id: UUID, limit: int = 100, offset: int = 0) -> list[TransferDB]:
        """Retrieve transfer history for a specific account.

        Args:
            account_id: UUID of the account to get transfers for
            limit: Maximum number of transfers to return (for pagination)
            offset: Number of transfers to skip (for pagination)

        Returns:
            List of TransferDB instances where the account is either source or destination
        """
        transfers = (
            self.session.query(TransferDB)
            .filter(or_(TransferDB.source_account_id == account_id, TransferDB.destination_account_id == account_id))
            .order_by(TransferDB.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        logger.info(f"Retrieved {len(transfers)} transfers for account {account_id}")
        return transfers

    def get_transfer_by_idempotency_key(self: Self, idempotency_key: UUID) -> TransferDB | None:
        """Retrieve a transfer by its idempotency key.

        Args:
            idempotency_key: UUID used as idempotency key for the transfer

        Returns:
            TransferDB instance if found, None otherwise
        """
        transfer = self.session.query(TransferDB).filter(TransferDB.idempotency_key == idempotency_key).first()

        if transfer:
            logger.info(f"Found existing transfer {transfer.id} with idempotency key {idempotency_key}")

        return transfer

    def update_transfer_status(self: Self, transfer_id: UUID, transfer_status: TransferStatus) -> TransferDB:
        """Update the status of a transfer.

        Args:
            transfer_id: UUID of the transfer to update
            transfer_status: New status for the transfer

        Returns:
            Updated TransferDB instance

        Raises:
            AppError: If transfer not found
        """
        transfer = self.get_transfer(transfer_id)

        prev_status = transfer.status
        transfer.status = transfer_status

        try:
            self.session.commit()
            self.session.refresh(transfer)

            logger.info(f"Updated transfer {transfer_id} status from {prev_status} to {transfer_status}")
            return transfer

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update transfer {transfer_id} status: {e}")
            raise AppError(
                AppErrorType.ERROR_DATABASE,
                detail="Failed to update transfer status",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
