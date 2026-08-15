from pydantic import BaseModel, Field, field_validator
import re

class UserRegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)

    @field_validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v

class ExperimentSchema(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    student_id: str = Field(..., min_length=4, max_length=15)
    status: str = Field(...)