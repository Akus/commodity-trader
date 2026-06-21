"""Commodity quote endpoints."""

from fastapi import APIRouter, HTTPException

from ..models import Quote
from ..store import store

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("", response_model=list[Quote])
def list_quotes() -> list[Quote]:
    return store.list_quotes()


@router.get("/{symbol}", response_model=Quote)
def get_quote(symbol: str) -> Quote:
    quote = store.get_quote(symbol)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"unknown symbol '{symbol}'")
    return quote
