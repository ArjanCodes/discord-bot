import motor.motor_asyncio as motor
from bson import datetime


def get_date() -> datetime.datetime:
    return datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

class UserStatCollectionHandler(motor.AsyncIOMotorCollection):
    def __init__(self, database) -> None:
        super().__init__(database, "users")

    async def insert(self, channel_id: int, user_id: int) -> None:
        await self.update_one(
            {"day": get_date(), "user_id": user_id, "channel_id": channel_id},
            {"$inc": {"count": 1}},
            True,
        )

    async def find_by_user(self, user_id: int):
        return await self.aggregate(
            [
                {"$match": {"user_id": user_id}},
                {
                    "$group": {
                        "_id": {"day": "$day", "user_id": "$user_id"},
                        "total": {"$sum": "$count"},
                    }
                },
                {"$project": {"day": "$_id.day", "total": 1, "_id": 0}},
            ]
        ).to_list(length=None)

    async def find_by_channel(self, channel_id: int):
        return await self.aggregate(
            [
                {"$match": {"channel_id": channel_id}},
                {
                    "$group": {
                        "_id": {"day": "$day", "channel_id": "$channel_id"},
                        "total": {"$sum": "$count"},
                    }
                },
                {"$project": {"day": "$_id.day", "total": 1, "_id": 0}},
            ]
        ).to_list(length=None)
