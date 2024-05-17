from fastapi import APIRouter, Depends

from app.api.dependencies.database import get_repository
from app.db.repositories.tags import TagsRepository
from app.models.schemas.tags import TagsInList
from typing import List
from pymongo.collection import Collection

router = APIRouter()


@router.get("", response_model=TagsInList, name="tags:get-all")
async def get_all_tags(
    tags_repo: TagsRepository = Depends(get_repository(TagsRepository)),
) -> TagsInList:
    tags_collection: Collection = tags_repo.tags_collection
    tags = await tags_collection.find({}, {"_id": 0, "tag": 1})
    tags_list = [tag["tag"] async for tag in tags]
    return TagsInList(tags=tags_list)
