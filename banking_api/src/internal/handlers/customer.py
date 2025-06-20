from fastapi.param_functions import Depends
from fastapi.routing import APIRouter
from internal.dependencies.customer import get_customer_service
from internal.models.customer import CustomerFindResponse
from internal.service.customer import CustomerService

router: APIRouter = APIRouter()


@router.get("/customers", response_model=list[CustomerFindResponse], summary="Get all customers.")
def get_all_customers(customer_service: CustomerService = Depends(get_customer_service)) -> list[CustomerFindResponse]:
    """Get all customers"""
    customers = customer_service.get_all_customers()
    return customers


@router.post("/customers", response_model=CustomerFindResponse, summary="Create a new customer.")
def create_customer(
    name: str, customer_service: CustomerService = Depends(get_customer_service)
) -> CustomerFindResponse:
    """Create a new customer.

    - **name**: The name of the customer to be created.
    """
    customer = customer_service.create_customer(name)
    return customer
