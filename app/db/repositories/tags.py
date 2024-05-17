from typing import List, Sequence

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository

from pymongo.collection import Collection


class TagsRepository(BaseRepository):

    async def get_all_tags(self) -> List[str]:
        """Get all tags from the database."""
        from pymongo.collection import Collection
        collection: Collection = self.connection["tags"]
        tags_cursor = collection.find({}, {"_id": 0, "tag": 1})
        tags = [tag["tag"] for tag in await tags_cursor.to_list(length=None)]
        return tags

    async def create_tags_that_dont_exist(self, *, tags: Sequence[str]) -> None:
        """Creates new tags that don't exist in the database."""
        from pymongo.collection import Collection
        collection: Collection = ...  # assume this is the tags collection
        for tag in tags:
            collection.update_one({"tag": tag}, {"$setOnInsert": {"tag": tag, "articles": []}}, upsert=True)
