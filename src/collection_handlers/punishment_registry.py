from src.cogs import PunishmentID

from bson import ObjectId
import motor.motor_asyncio as motor


class PunishmentRegistry(motor.AsyncIOMotorCollection):
    name: str = "punishmentRegistry"

    def __init__(self, database, **kwargs):
        super().__init__(database, self.name, **kwargs)

    async def new_punishment(self, _id: ObjectId, to_insert: dict) -> None:
        await self.insert_one({"_id": _id, **to_insert})

    async def count_total_amount(self) -> int:
        return await self.count_documents({})

    async def count_type(self, pun_type: PunishmentID) -> int:
        return await self.count_documents({"punishment_id": pun_type.value})

    async def count_by_user(self, user_id: int) -> int:
        return await self.count_documents({"user_id": user_id})

    async def count_type_by_user(self, user_id: int, pun_type: PunishmentID) -> int:
        return await self.count_documents(
            {"user_id": user_id, "punishment_id": pun_type.value}
        )

    async def get_info(self, _id: str) -> dict:
        return await self.find_one({"_id": ObjectId(_id)})
