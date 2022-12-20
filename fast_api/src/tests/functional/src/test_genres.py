import pytest

from config import test_settings
from models.models import Genre
from testdata.data_genres import test_genres


@pytest.mark.asyncio
class TestGenre:
    async def test_genres(self, set_up_genres, make_get_request):
        response = await make_get_request("genres")
        assert response.status == 200
        genres = [Genre(**genre) for genre in test_genres]
        assert genres[0] == response.body["genres"][0]

    async def test_genres_validate_page_size(self, set_up_persons, make_get_request):
        page_number = 1
        page_size = -40

        response = await make_get_request(
            "genres", page_number=page_number, page_size=page_size
        )
        assert response.status == 422

    async def test_genres_validate_page_number(self, set_up_genres, make_get_request):
        page_number = "test"
        page_size = 20

        response = await make_get_request(
            "genres", page_number=page_number, page_size=page_size
        )
        assert response.status == 422

    async def test_genres_page_more_than_exists(
            self, set_up_genres, make_get_request
    ):
        page_number = 20
        page_size = 20
        response = await make_get_request(
            "genres", page_number=page_number, page_size=page_size
        )
        assert response.status == 404

    async def test_current_genre(self, set_up_genres, make_get_request):
        genre = Genre(**test_genres[0])
        response = await make_get_request(f"genres/{genre.id}")
        assert response.status == 200 and genre == response.body

    async def test_genre_doesnt_exist(self, set_up_genres, make_get_request):
        genre_id = "doesnt_exist"
        response = await make_get_request(
            end_of_url=f"genres/{genre_id}"
        )
        assert response.status == 404

    async def test_cache_current_genre(self, set_up_genres, make_get_request, es_delete_data, es_write_data):
        await es_write_data(test_genres, test_settings.genre_index)
        genre = Genre(**test_genres[0])

        await es_delete_data(test_settings.genre_index)
        response = await make_get_request(f"genres/{genre.id}")

        assert response.status == 200 and genre == response.body
