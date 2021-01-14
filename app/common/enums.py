from enum import Enum


class ProxyStatus(str, Enum):
    CREATING = "creating"
    PREPARING = "preparing"
    UP = "up"
    BURNED = "burned"
    DOWN = "down"


class ClassifierPatternType(str, Enum):
    BODY_REQUIRED = "body_required"
    TITLE_DOWN = "title_down"
    BODY_DOWN = "body_down"
    BODY_BLOCKED = "body_blocked"


class CheckStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    BLOCKED = "blocked"
