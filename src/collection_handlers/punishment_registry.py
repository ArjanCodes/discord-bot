from pymongo import collection
from bson import ObjectId

from src.cogs.punishments import PunishmentID


class PunishmentRegistry(collection.Collection):
    name: str = "punishmentRegistry"

    def __init__(self, database, **kwargs):
        super().__init__(database, self.name, **kwargs)

    def new_punishment(self, _id: ObjectId, to_insert: dict) -> None:
        self.insert_one({"_id": _id, **to_insert})

    def count_total_amount(self) -> int:
        return self.count_documents({})

    def count_type(self, pun_type: PunishmentID) -> int:
        return self.count_documents({"punishment_id": pun_type.value})

    def count_by_user(self, user_id: int) -> int:
        return self.count_documents({"user_id": user_id})

    def count_type_by_user(self, user_id: int, pun_type: PunishmentID) -> int:
        return self.count_documents(
            {"user_id": user_id, "punishment_id": pun_type.value}
        )
