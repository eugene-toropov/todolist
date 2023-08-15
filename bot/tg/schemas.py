from pydantic import BaseModel, Field


class Chat(BaseModel):
    id: int
    # first_name: str
    # last_name: str
    username: str | None = None
    # type: str


# class MessageFrom(BaseModel):
#     id: int
#     is_bot: bool
#     first_name: str = None
#     last_name: str = None
#     username: str
#     language_code: str = None


# class Entities(BaseModel):
#     offset: int
#     length: int
#     type: str


class Message(BaseModel):
    message_id: int
    # from_: MessageFrom = Field(alias='from')
    chat: Chat
    # date: int
    # edit_date: int | None = None
    text: str
    # entities: list[Entities] | None = None

    # class Config:
    #     allow_population_by_field_name = True


class Update(BaseModel):
    update_id: int
    message: Message


class GetUpdatesResponse(BaseModel):
    ok: bool
    result: list[Update] = []


class SendMessageResponse(BaseModel):
    ok: bool
    result: Message
