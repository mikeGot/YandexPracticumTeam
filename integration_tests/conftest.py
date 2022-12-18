from __future__ import annotations

import asyncio
from dataclasses import dataclass

import aiohttp
import pytest
from elasticsearch import AsyncElasticsearch, helpers
from integration_tests.config import test_settings
from integration_tests.testdata.data_search import test_data_films
from integration_tests.testdata.data_main_page import test_main_page_genres, test_films_main_page


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def es_write_data(es_client: AsyncElasticsearch):
    async def inner(data, index):
        bulk_query = get_es_bulk_query(data, index)
        await helpers.async_bulk(es_client, bulk_query, refresh="wait_for")
    return inner


@pytest.fixture
def es_delete_data(es_client: AsyncElasticsearch):
    async def inner(index):
        response = await es_client.delete_by_query(
            index=index, body={"query": {"match_all": {}}}
        )

    return inner


@pytest.fixture(scope="class")
async def set_up_search_films():
    client = AsyncElasticsearch(hosts=test_settings.es_host)
    bulk_query = get_es_bulk_query(test_data_films, test_settings.movie_index)
    await helpers.async_bulk(client, bulk_query, refresh="wait_for")
    yield client
    # await client.delete_by_query(index=test_settings.movie_index, body={"query": {"match_all": {}}})
    await client.close()


@pytest.fixture(scope="class")
async def set_up_main_page():
    client = AsyncElasticsearch(hosts=test_settings.es_host)
    bulk_query_films = get_es_bulk_query(test_films_main_page, test_settings.movie_index)
    await helpers.async_bulk(client, bulk_query_films, refresh="wait_for")

    bulk_query_genres = get_es_bulk_query(test_main_page_genres, test_settings.genre_index)
    await helpers.async_bulk(client, bulk_query_genres, refresh="wait_for")

    yield client
    # await client.delete_by_query(index=test_settings.movie_index, body={"query": {"match_all": {}}})
    # await client.delete_by_query(index=test_settings.genre_index, body={"query": {"match_all": {}}})
    await client.close()


@pytest.fixture
async def es_client():
    client = AsyncElasticsearch(hosts=test_settings.es_host)
    yield client
    await client.close()


def get_es_bulk_query(es_data, index):
    data = []
    for item in es_data:
        data.append({"_id": item["id"], "_index": index, "_source": item})
    return data


@dataclass
class Response:
    body: list[dict]
    status: int


@pytest.fixture
def make_get_request():
    async def inner(
        end_of_url,
        query: str | None = None,
        page_number: int | str | None = None,
        page_size: int | str | None = None,
        sort: str | None = None,
        genre: str | None = None
    ) -> Response:
        session = aiohttp.ClientSession()
        url = test_settings.service_url + "/api/v1/" + str(end_of_url)
        query_data = {}
        if query:
            query_data["query"] = str(query)
        if page_number:
            query_data["page[number]"] = page_number
        if page_size:
            query_data["page[size]"] = page_size
        if sort:
            query_data["sort"] = str(sort)
        if genre:
            query_data["filter[genre]"] = str(genre)

        async with session.get(url, params=query_data) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        await session.close()
        return Response(body=body, status=status)

    return inner
