from pydantic import BaseModel


class ProvcodeBase(BaseModel):
    provcode: str

    # class Config:
    #     orm_mode = True

    # ให้สารถเรียกใช้งาน .get ได้
    def get(self, key):
        return getattr(self, key, None)
