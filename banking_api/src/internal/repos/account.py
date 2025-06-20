import logging
from typing import Self
from uuid import UUID

from fastapi import HTTPException, status
from internal.helpers.app_exceptions import AppError, AppErrorType
from internal.models.account import AccountDB
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.session import Session


class AccountRepo:
    def __init__(self: Self, session: Session) -> None:
        self.session: Session = session

    def create_account(self: Self, item: AccountDB) -> AccountDB:
        """Create a new account in the database.

        Args:
            item: AccountDB instance to create
        Returns:
            Created AccountDB instance
        Raises:
            AppError: If a unique constraint violation occurs
        """
        try:
            self.session.add(item)
            self.session.commit()
            self.session.refresh(item)

        except DBAPIError as e:
            if e.orig is not None and AppErrorType.ERROR_UNIQUE_CONSTRAINT.value in e.orig.args[0].get("M"):
                raise AppError(
                    AppErrorType.ERROR_UNIQUE_CONSTRAINT,
                    detail="" if len(e.orig.args) == 0 else e.orig.args[0].get("D"),
                    status_code=status.HTTP_400_BAD_REQUEST,
                ) from e
            logging.error(f"{e=!r}")
            raise e

        except Exception as e:
            logging.error(f"{e=!r}")
            raise e

        return item

    def get_account(self: Self, account_id: UUID) -> AccountDB:
        """Get an account by its ID.

        Args:
            account_id: UUID of the account to retrieve
        Returns:
            AccountDB instance
        Raises:
            HTTPException: If the account is not found
        """
        account: AccountDB | None = self.session.query(AccountDB).filter(AccountDB.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        return account

    def get_all_accounts(self: Self) -> list[AccountDB]:
        """Get all accounts in the database.

        Returns:
            List of AccountDB instances
        """
        accounts: list[AccountDB] = self.session.query(AccountDB).all()
        return accounts

    def update_account_balance(self: Self, account_id: UUID, new_balance: float) -> AccountDB:
        """Update an account's balance with optimistic concurrency control.

        Args:
            account_id: UUID of the account to update
            new_balance: New balance value

        Returns:
            Updated AccountDB instance

        Raises:
            AppError: If account not found or concurrent update detected
        """
        try:
            # Get the current account with FOR UPDATE lock to prevent concurrent modification
            account = self.session.query(AccountDB).filter(AccountDB.id == account_id).with_for_update().first()

            if not account:
                raise AppError(
                    AppErrorType.ERROR_NOT_FOUND,
                    detail="Account not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            # Update the balance and increment the version
            account.current_balance = new_balance
            account.version += 1

            # Flush changes to get any database errors early
            self.session.flush()
            self.session.commit()
            self.session.refresh(account)

            return account

        except AppError:
            raise
        except Exception:
            raise AppError(
                AppErrorType.ERROR_DATABASE,
                detail="Failed to update account balance. Please try again.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
