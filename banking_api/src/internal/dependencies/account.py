from fastapi import Depends
from internal.database.postgresql import get_session
from internal.repos.account import AccountRepo
from internal.repos.customer import CustomerRepo
from internal.repos.transfer import TransferRepo
from internal.service.account import AccountService
from sqlalchemy.orm import Session


def get_database_session() -> Session:
    session = next(get_session())
    try:
        yield session
    finally:
        session.close()


def get_account_repo(session: Session = Depends(get_database_session)) -> AccountRepo:
    return AccountRepo(session=session)


def get_customer_repo(session: Session = Depends(get_database_session)) -> CustomerRepo:
    return CustomerRepo(session=session)


def get_transfer_repo(session: Session = Depends(get_database_session)) -> TransferRepo:
    return TransferRepo(session=session)


def get_account_service(
    session: Session = Depends(get_database_session),
    customer_repo: CustomerRepo = Depends(get_customer_repo),
    account_repo: AccountRepo = Depends(get_account_repo),
    transfer_repo: TransferRepo = Depends(get_transfer_repo),
) -> AccountService:
    return AccountService(
        session=session, customer_repo=customer_repo, account_repo=account_repo, transfer_repo=transfer_repo
    )
