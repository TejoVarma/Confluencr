from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_expense_service
from app.core.errors import AppError
from app.schemas.expense import (
    Expense,
    ExpenseCreate,
    ExpenseListQuery,
    ExpenseListResponse,
    MonthlySummary,
    SummaryQuery,
)
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])

# Handlers are sync on purpose: the Supabase client is blocking, so FastAPI runs them in a threadpool.


@router.post("", response_model=Expense, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, service: ExpenseService = Depends(get_expense_service)):
    return service.create(payload)


@router.get("", response_model=ExpenseListResponse)
def list_expenses(
    category: str | None = None,
    date_from: str | None = Query(None, alias="from"),
    date_to: str | None = Query(None, alias="to"),
    page: str | None = None,
    limit: str | None = None,
    service: ExpenseService = Depends(get_expense_service),
):
    query = ExpenseListQuery.model_validate(
        {"category": category, "date_from": date_from, "date_to": date_to, "page": page, "limit": limit}
    )
    return service.list(query)


@router.get("/summary", response_model=MonthlySummary)
def monthly_summary(month: str | None = None, service: ExpenseService = Depends(get_expense_service)):
    query = SummaryQuery.model_validate({"month": month})
    return service.monthly_summary(query.month)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: str, service: ExpenseService = Depends(get_expense_service)):
    try:
        UUID(expense_id)
    except ValueError:
        raise AppError("id must be a valid UUID", 400) from None
    service.delete(expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
