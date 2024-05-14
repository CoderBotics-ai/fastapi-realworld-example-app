from typing import List, Sequence

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from typing import List
from bson.objectid import ObjectId
from pymongo import MongoClient




class TagsRepository(BaseRepository):

    async def get_all_tags(self) -> List[str]:
        collection = self.db['articles']  # Assuming the tags are stored in the 'articles' collection
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$project": {"_id": 0, "tag": "$_id"}}
        ]
        tags_cursor = collection.aggregate(pipeline)
        tags = [tag['tag'] async for tag in tags_cursor]
        return tags

    async def create_tags_that_dont_exist(self, *, tags: Sequence[str]) -> None:
        await queries.create_new_tags(self.connection, [{"tag": tag} for tag in tags])

    def __init__(self, client: MongoClient):
        self.db = client['your_database_name']  # Replace with your actual database name
