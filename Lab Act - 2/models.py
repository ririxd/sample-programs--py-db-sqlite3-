from pydantic import BaseModel, confloat, conint, constr, validator


class UserRegistration(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=50)
    password: constr(min_length=8)


class UserLogin(BaseModel):
    username: constr(strip_whitespace=True, min_length=1, max_length=50)
    password: constr(min_length=1)


class HardwareCreate(BaseModel):
    item_name: constr(strip_whitespace=True, min_length=1, max_length=100)
    category: constr(strip_whitespace=True, min_length=1, max_length=50)
    quantity: conint(ge=0)
    unit_price: confloat(ge=0)

    @validator("item_name", "category")
    def strip_text(cls, value: str) -> str:
        return value.strip()


class HardwareUpdate(BaseModel):
    item_id: conint(ge=1)
    quantity: conint(ge=0)
    unit_price: confloat(ge=0)
