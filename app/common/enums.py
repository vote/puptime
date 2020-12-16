from enum import Enum

class ProxyStatus(Enum):
    CREATING = "creating"
    PREPARING = "preparing"
    UP = "up"
    BURNED = "burned"
    DOWN = "down"
