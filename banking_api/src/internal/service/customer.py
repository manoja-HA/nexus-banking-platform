from uuid import UUID

from internal.models.customer import CustomerFindResponse
from internal.repos.customer import CustomerRepo


class CustomerService:
    def __init__(self, customer_repo: CustomerRepo):
        self.customer_repo = customer_repo

    def create_customer(self, name: str) -> CustomerFindResponse:
        customer = self.customer_repo.create_customer(name)
        return CustomerFindResponse.model_validate(customer)

    def get_customer(self, customer_id: UUID) -> CustomerFindResponse:
        customer = self.customer_repo.get_customer(customer_id)
        return CustomerFindResponse.model_validate(customer)

    def get_all_customers(self) -> list[CustomerFindResponse]:
        customers = self.customer_repo.get_all_customers()
        return [CustomerFindResponse.model_validate(customer) for customer in customers]
