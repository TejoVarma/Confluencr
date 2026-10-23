from fastapi import Depends

from app.db.supabase import get_supabase_client
from app.repositories.expense_repo import ExpenseRepository, SupabaseExpenseRepository
from app.services.expense_service import ExpenseService


def get_expense_repository() -> ExpenseRepository:
    return SupabaseExpenseRepository(get_supabase_client())


def get_expense_service(repo: ExpenseRepository = Depends(get_expense_repository)) -> ExpenseService:
    return ExpenseService(repo)
