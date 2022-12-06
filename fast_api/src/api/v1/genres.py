from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.models.models import Genre
from core.config import settings
from services.genre import GenreService, get_genre_service
from api.constants.error_msgs import GenreMsg

router = APIRouter()


@router.get(
    "/",
    response_model=list[Genre],
    summary='Get Genres',
    description='Get list of genres (page by page)'
)
async def genre_list(
    request: Request,
    page_number: int | None = Query(alias="page[number]", ge=1, default=1),
    page_size: int
    | None = Query(alias="page[size]", ge=1, default=settings.pagination_size),
    film_service: GenreService = Depends(get_genre_service),
) -> list[Genre]:
    url = request.url.path + request.url.query
    genres = await film_service.get_list_genres(url, page_number, page_size)
    if not genres:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=GenreMsg.no_search_result
        )
    return genres


@router.get(
    "/{genre_id}",
    response_model=Genre,
    description='Get Genre by ID'
)
async def genre_details(
    request: Request,
    genre_id: str, film_service: GenreService = Depends(get_genre_service)
) -> Genre:
    url = request.url.path + request.url.query
    genre = await film_service.get_genre_by_id(url, genre_id)
    if not genre:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=GenreMsg.not_found_by_id
        )
    return genre
