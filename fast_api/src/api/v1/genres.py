from __future__ import annotations

import math
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.constants.error_msgs import GenreMsg
from api.models.models import Genre, GenresWithPaging
from core.config import settings
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get(
    "",
    response_model=GenresWithPaging,
    summary="Get Genres",
    description="Get list of genres (page by page)",
)
async def genre_list(
    request: Request,
    page_number: int | None = Query(default=1, alias="page[number]", ge=1),
    page_size: int
    | None = Query(default=settings.pagination_size, alias="page[size]", ge=1),
    genre_service: GenreService = Depends(get_genre_service),
) -> GenresWithPaging:
    url = request.url.path + request.url.query
    genres, total_items = await genre_service.get_list_genres(
        url, page_number, page_size
    )
    if not genres:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=GenreMsg.no_search_result
        )

    total_pages = math.ceil(total_items / page_size)

    return GenresWithPaging(
        genres=genres, total_pages=total_pages, total_items=total_items
    )


@router.get("/{genre_id}", response_model=Genre, description="Get Genre by ID")
async def genre_details(
    request: Request,
    genre_id: str,
    genre_service: GenreService = Depends(get_genre_service),
) -> Genre:
    url = request.url.path + request.url.query
    genre = await genre_service.get_genre_by_id(url, genre_id)
    if not genre:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=GenreMsg.not_found_by_id
        )
    return genre
