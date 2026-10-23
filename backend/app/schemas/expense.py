"""Request/response models.

Validation rules here are mirrored in frontend/src/features/expenses/validation.ts.
"""

import datetime as dt
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.clock import today

Category = Literal["food", "travel", "bills", "other"]
CATEGORIES: tuple[str, ...] = get_args(Category)

TITLE_MAX_LENGTH = 100
MAX_AMOUNT = Decimal("9999999999.99")  # numeric(12, 2)
DEFAULT_LIMIT = 10
MAX_LIMIT = 100

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_POSITIVE_INT_RE = re.compile(r"^\d+$")
_CATEGORY_ERROR = f"category must be one of: {', '.join(CATEGORIES)}"


def parse_iso_date(value: Any, field: str) -> dt.date:
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError(f"{field} must be a date in YYYY-MM-DD format")
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be a valid date") from None


def _parse_category(value: Any) -> str:
    if value not in CATEGORIES:
        raise ValueError(_CATEGORY_ERROR)
    return value


class ExpenseCreate(BaseModel):
    title: str
    amount: Decimal
    category: Category
    date: dt.date | None = None

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("title must be a string")
        value = value.strip()
        if not value:
            raise ValueError("title is required")
        if len(value) > TITLE_MAX_LENGTH:
            raise ValueError(f"title must be at most {TITLE_MAX_LENGTH} characters")
        return value

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: Any) -> Decimal:
        # Only real JSON numbers are accepted — no strings or booleans.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("amount must be a number")
        try:
            amount = Decimal(str(value))
        except InvalidOperation:
            raise ValueError("amount must be a number") from None
        if not amount.is_finite():
            raise ValueError("amount must be a number")
        if amount <= 0:
            raise ValueError("amount must be greater than 0")
        if amount.as_tuple().exponent < -2:
            raise ValueError("amount must have at most 2 decimal places")
        if amount > MAX_AMOUNT:
            raise ValueError(f"amount must be at most {MAX_AMOUNT}")
        return amount

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, value: Any) -> str:
        return _parse_category(value)

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, value: Any) -> dt.date | None:
        if value is None:
            return None
        parsed = parse_iso_date(value, "date")
        if parsed > today():
            raise ValueError("date cannot be in the future")
        return parsed


class ExpenseListQuery(BaseModel):
    """Query params for GET /expenses. Raw strings in, so error messages stay ours."""

    category: Category | None = None
    date_from: dt.date | None = None
    date_to: dt.date | None = None
    page: int = 1
    limit: int = DEFAULT_LIMIT

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, value: Any) -> str | None:
        return None if value in (None, "") else _parse_category(value)

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def validate_dates(cls, value: Any, info) -> dt.date | None:
        name = "from" if info.field_name == "date_from" else "to"
        return None if value in (None, "") else parse_iso_date(value, name)

    @field_validator("page", mode="before")
    @classmethod
    def validate_page(cls, value: Any) -> int:
        if value in (None, ""):
            return 1
        if not isinstance(value, str) or not _POSITIVE_INT_RE.match(value) or int(value) < 1:
            raise ValueError("page must be a positive integer")
        return int(value)

    @field_validator("limit", mode="before")
    @classmethod
    def validate_limit(cls, value: Any) -> int:
        if value in (None, ""):
            return DEFAULT_LIMIT
        if (
            not isinstance(value, str)
            or not _POSITIVE_INT_RE.match(value)
            or not 1 <= int(value) <= MAX_LIMIT
        ):
            raise ValueError(f"limit must be an integer between 1 and {MAX_LIMIT}")
        return int(value)

    @model_validator(mode="after")
    def validate_range(self) -> "ExpenseListQuery":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("from must be on or before to")
        return self


class SummaryQuery(BaseModel):
    month: str

    @field_validator("month", mode="before")
    @classmethod
    def validate_month(cls, value: Any) -> str:
        if value in (None, ""):
            raise ValueError("month is required (YYYY-MM)")
        if not isinstance(value, str) or not _MONTH_RE.match(value):
            raise ValueError("month must be in YYYY-MM format")
        return value


class Expense(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    amount: float
    category: Category
    date: dt.date
    created_at: str | None = None


class ExpenseListResponse(BaseModel):
    items: list[Expense]
    total_count: int
    total_amount: float


class MonthlySummary(BaseModel):
    month: str
    totals: dict[Category, float]
    total: float
