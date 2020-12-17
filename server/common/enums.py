from enum import Enum

class ProxyStatus(str, Enum):
    CREATING = "creating"
    PREPARING = "preparing"
    UP = "up"
    BURNED = "burned"
    DOWN = "down"
