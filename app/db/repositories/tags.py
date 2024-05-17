from typing import List, Sequence

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository

from pymongo.collection import Collection


class TagsRepository(BaseRepository):

    async def get_all_tags(self) -> List[str]:
        """Get all tags from the database."""
        from pymongo.collection import Collection
        collection: Collection = self.connection  # Assuming self.connection is a pymongo collection
        tags_cursor = collection.aggregate([{"$unwind": "$tags"}, {"$group": {"_id": "$tags"}}])
        tags = [tag["_id"] for tag in await tags_cursor.to_list(length=None)]
        return tags

    async def create_tags_that_dont_exist(self, *, tags: Sequence[str]) -> None:
        """Creates new tags that don't exist in the database."""
        from pymongo.collection import Collection
        collection: Collection = ...  # assume collection is defined
        await collection.insert_many([{"tag": tag} for tag in tags], ordered=False)
