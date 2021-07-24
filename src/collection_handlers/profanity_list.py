import motor.motor_asyncio as motor

from enum import Enum, unique
from typing import List


@unique
class ListType(Enum):
    BASE_LIST = "baseList"


@unique
class DocumentType(Enum):
    REPORT = "REPORT"
    BLACKLIST = "BLACKLIST"


class ProfanityListStorage(motor.AsyncIOMotorCollection):
    name: str = "profanityList"

    def __init__(self, database, **kwargs):
        super().__init__(database, self.name, **kwargs)

    async def words(self, list_type: ListType = ListType.BASE_LIST) -> List[str]:
        data = await self.find_one(
            {"listType": list_type.value}, {"words": 1, "_id": 0}
        )
        return data.get("words")

    async def remove(
        self, to_remove: set, list_type: ListType = ListType.BASE_LIST
    ) -> None:
        await self.update_one(
            {"listType": list_type.value},
            {"$pull": {"words": {"$in": list(to_remove)}}},
        )

    async def add(self, to_add: set, list_type: ListType = ListType.BASE_LIST) -> None:
        await self.update_one(
            {"listType": list_type.value},
            {"$push": {"words": {"$each": list(to_add)}}},
        )

    @property
    async def reports(self) -> List[dict]:
        report_dict = await self.find_one(
            {"documentType": DocumentType.REPORT.value}, {"_id": 0, "reports": 1}
        )
        return report_dict.get("reports")

    async def get_report(self, message_id: int) -> dict:
        for report in await self.reports:
            if report["message_id"] == message_id:
                return report

    async def add_report(self, message_id: int, profanities: set) -> None:
        await self.update_one(
            {"documentType": DocumentType.REPORT.value},
            {"$push": {"reports": self.construct_report(message_id, profanities)}},
        )

    async def remove_report(self, message_id: int) -> None:
        await self.update_one(
            {"documentType": DocumentType.REPORT.value},
            {"$pull": {"reports": {"message_id": {"$eq": message_id}}}},
        )

    @staticmethod
    def construct_report(message_id: int, profanities: set) -> dict:
        return {"message_id": message_id, "profanities": list(profanities)}
