from typing import Self
from uuid import UUID

from fastapi import HTTPException, status
from internal.models.customer import CustomerDB
from sqlalchemy.orm.session import Session


class CustomerRepo:
    def __init__(self: Self, session: Session) -> None:
        self.session: Session = session

    def create_customer(self: Self, name: str) -> CustomerDB:
        """Create a new customer in the database.
        :param name: The name of the customer.
        :return: The created customer.
        """
        customer = self.session.query(CustomerDB).filter(CustomerDB.name == name).first()
        if customer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer already exists")
        customer: CustomerDB = CustomerDB(name=name)
        self.session.add(customer)
        self.session.commit()
        self.session.refresh(customer)
        return customer

    def get_customer(self: Self, customer_id: UUID) -> CustomerDB:
        """Get a customer by ID.
        :param customer_id: The ID of the customer.
        :return: The customer with the given ID.
        """
        customer: CustomerDB | None = self.session.query(CustomerDB).filter(CustomerDB.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer

    def get_all_customers(self: Self) -> list[CustomerDB]:
        """Get all customers from the database.
        :return: A list of all customers.
        """
        customers: list[CustomerDB] = self.session.query(CustomerDB).all()
        return customers
