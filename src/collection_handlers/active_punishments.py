from bson import ObjectId

from datetime import datetime
import motor.motor_asyncio as motor
from src.cogs import PunishmentID


class ActivePunishments(motor.AsyncIOMotorCollection):
    name: str = "activePunishments"

    def __init__(self, database, **kwargs):
        super().__init__(database, self.name, **kwargs)

    async def new_punishment(self, _id: ObjectId, to_insert: dict) -> None:
        await self.insert_one({"registry_id": _id, **to_insert})

    async def get_to_deactivate(self):
        return self.find({"expires_at": {"$lte": datetime.now()}})

    async def deactivate(self) -> None:
        await self.delete_many({"expires_at": {"$lte": datetime.now()}})

    async def has_active_mute(self, user_id: int) -> bool:
        return (
            await self.find_one(
                {"user_id": user_id, "punishment_id": PunishmentID.MUTE.value}
            )
            is not None
        )

    async def count_total_amount(self) -> int:
        return await self.count_documents({})

    async def count_type(self, punishment_type: PunishmentID) -> int:
        return await self.count_documents({"punishment_id": punishment_type.value})
