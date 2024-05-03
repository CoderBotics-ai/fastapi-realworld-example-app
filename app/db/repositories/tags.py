from typing import List, Sequence

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository

from pymongo import MongoClient
from typing import List




class TagsRepository(BaseRepository):

    async def get_all_tags(self) -> List[str]:
        tags_collection = self.db.get_collection('tags')
        cursor = tags_collection.find({}, {'tag': 1, '_id': 0})
        tags = await cursor.to_list(length=None)
        return [tag['tag'] for tag in tags]

    async def create_tags_that_dont_exist(self, *, tags: Sequence[str]) -> None:
        await queries.create_new_tags(self.connection, [{"tag": tag} for tag in tags])
