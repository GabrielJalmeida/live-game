from enum import StrEnum


class EventType(StrEnum):
    COMMENT = "COMMENT"
    GIFT = "GIFT"
    LIKE = "LIKE"
    FOLLOW = "FOLLOW"
    SHARE = "SHARE"
    JOIN = "JOIN"
    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"