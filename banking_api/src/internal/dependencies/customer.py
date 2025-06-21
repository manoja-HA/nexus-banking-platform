from fastapi import Depends
from internal.database.postgresql import get_session
from internal.repos.customer import CustomerRepo
from internal.service.customer import CustomerService
from sqlalchemy.orm import Session


def get_customer_repo(session: Session = Depends(get_session)) -> CustomerRepo:
    return CustomerRepo(session=session)


def get_customer_service(customer_repo: CustomerRepo = Depends(get_customer_repo)) -> CustomerService:
    return CustomerService(customer_repo=customer_repo)
