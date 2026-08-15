from pydantic import BaseModel, Field, field_validator
import re


class UserRegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_]+", value):
            raise ValueError("Username must be alphanumeric and may include underscores")
        return value


class ExperimentSchema(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    student_id: str = Field(..., min_length=4, max_length=15)
    status: str = Field(...)
