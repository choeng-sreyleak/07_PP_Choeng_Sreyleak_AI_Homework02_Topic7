"""Input validation schemas for the shopping tools.

Responsibilities:
- define the allowed structure for each tool input
- validate values such as positive product IDs and valid quantity ranges
- provide the schema registry used by the harness
"""

from pydantic import BaseModel, Field, field_validator


class SearchProductInput(BaseModel):
    query: str = Field(..., description="Product name or keyword to search for")

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("query must not be empty")
        return v.strip()


class CheckStockInput(BaseModel):
    product_id: int = Field(..., description="ID of the product to check")

    @field_validator("product_id")
    @classmethod
    def id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("product_id must be a positive integer")
        return v


class GetProductInput(BaseModel):
    product_id: int = Field(..., description="ID of the product to inspect")

    @field_validator("product_id")
    @classmethod
    def id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("product_id must be a positive integer")
        return v


class BuyProductInput(BaseModel):
    product_id: int = Field(..., description="ID of the product to purchase")
    quantity: int = Field(..., description="How many units to purchase")

    @field_validator("product_id")
    @classmethod
    def id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("product_id must be a positive integer")
        return v

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity must be a positive integer")
        if v > 50:
            raise ValueError("quantity exceeds the per-order limit (50)")
        return v


class DeleteProductInput(BaseModel):
    product_id: int = Field(..., description="ID of the product to remove from the catalog")

    @field_validator("product_id")
    @classmethod
    def id_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("product_id must be a positive integer")
        return v


SCHEMA_REGISTRY = {
    "search_product": SearchProductInput,
    "check_stock": CheckStockInput,
    "get_product": GetProductInput,
    "buy_product": BuyProductInput,
    "delete_product": DeleteProductInput,
}

