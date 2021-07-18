from pymongo import collection, cursor
from bson import ObjectId

from datetime import datetime

from src.cogs import PunishmentID

class ActivePunishments(collection.Collection):
    name: str = "activePunishments"

    def __init__(self, database, **kwargs):
        super().__init__(database, self.name, **kwargs)

    def new_punishment(self, _id: ObjectId, to_insert: dict) -> None:
        self.insert_one({"registry_id": _id, **to_insert})

    def get_to_deactivate(self) -> cursor.Cursor:
        return self.find({"expires_at": {"$lte": datetime.now()}})

    def deactivate(self) -> None:
        self.delete_many({"expires_at": {"$lte": datetime.now()}})

    def has_active_mute(self, user_id: int) -> bool:
        return (
            self.find({"user_id": user_id, "punishment_id": PunishmentID.MUTE.value})
            is not None
        )

    def count_total_amount(self) -> int:
        return self.count_documents({})

    def count_type(self, punishment_type: PunishmentID) -> int:
        return self.count_documents({"punishment_id": punishment_type.value})
