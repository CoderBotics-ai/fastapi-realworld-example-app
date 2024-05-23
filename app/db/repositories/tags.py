from typing import List, Sequence

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from typing import List
from pymongo.collection import Collection


class TagsRepository(BaseRepository):

    async def get_all_tags(self) -> List[str]:
        tags_collection: Collection = self.connection['tags']
        tags_cursor = tags_collection.find({}, {'_id': 0, 'tag': 1})
        tags_row = await tags_cursor.to_list(length=None)
        return [tag['tag'] for tag in tags_row]


    async def create_tags_that_dont_exist(self, *, tags: Sequence[str]) -> None:
        tags_collection: Collection = self.connection["tags"]
        existing_tags = await tags_collection.find({"tag": {"$in": tags}}).to_list(length=None)
        existing_tag_names = {tag["tag"] for tag in existing_tags}
        new_tags = [{"tag": tag} for tag in tags if tag not in existing_tag_names]
        if new_tags:
            await tags_collection.insert_many(new_tags)
