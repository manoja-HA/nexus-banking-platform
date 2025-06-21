from fastapi import Depends
from internal.database.postgresql import get_session
from internal.repos.account import AccountRepo
from internal.repos.transfer import TransferRepo
from internal.service.transfer import TransferService
from sqlalchemy.orm import Session


def get_account_repo(session: Session = Depends(get_session)) -> AccountRepo:
    return AccountRepo(session=session)


def get_transfer_repo(session: Session = Depends(get_session)) -> TransferRepo:
    return TransferRepo(session=session)


def get_transfer_service(
    account_repo: AccountRepo = Depends(get_account_repo), transfer_repo: TransferRepo = Depends(get_transfer_repo)
) -> TransferService:
    return TransferService(account_repo=account_repo, transfer_repo=transfer_repo)
