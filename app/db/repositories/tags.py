from typing import List, Sequence

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository








class TagsRepository(BaseRepository):

    async def get_all_tags(self) -> List[str]:
        tags_collection = self.db.get_collection('tags')
        cursor = tags_collection.find({}, {'tag': 1, '_id': 0})
        tags = [doc['tag'] for doc in await cursor.to_list(length=None)]
        return tags

    async def create_tags_that_dont_exist(self, *, tags: Sequence[str]) -> None:
        existing_tags = await self.db.tags.find({"tag": {"$in": tags}}, {"tag": 1}).to_list(None)
        existing_tags_set = {tag['tag'] for tag in existing_tags}
        new_tags = [{"tag": tag} for tag in tags if tag not in existing_tags_set]
        if new_tags:
            await self.db.tags.insert_many(new_tags)
