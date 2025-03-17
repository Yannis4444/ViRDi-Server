from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProductionOffer(_message.Message):
    __slots__ = ("resource_id",)
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    resource_id: str
    def __init__(self, resource_id: _Optional[str] = ...) -> None: ...

class ProductionRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResourceProduction(_message.Message):
    __slots__ = ("init_info", "amount")
    INIT_INFO_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    init_info: ResourceProductionInitInfo
    amount: int
    def __init__(self, init_info: _Optional[_Union[ResourceProductionInitInfo, _Mapping]] = ..., amount: _Optional[int] = ...) -> None: ...

class ResourceProductionInitInfo(_message.Message):
    __slots__ = ("resource_id",)
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    resource_id: str
    def __init__(self, resource_id: _Optional[str] = ...) -> None: ...

class ProductionResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConsumptionRequest(_message.Message):
    __slots__ = ("consumer_id", "resource_id", "max_rate", "current_buffer_amount", "buffer_limit")
    CONSUMER_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_RATE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_BUFFER_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    BUFFER_LIMIT_FIELD_NUMBER: _ClassVar[int]
    consumer_id: str
    resource_id: str
    max_rate: int
    current_buffer_amount: int
    buffer_limit: int
    def __init__(self, consumer_id: _Optional[str] = ..., resource_id: _Optional[str] = ..., max_rate: _Optional[int] = ..., current_buffer_amount: _Optional[int] = ..., buffer_limit: _Optional[int] = ...) -> None: ...

class ResourceConsumption(_message.Message):
    __slots__ = ("amount",)
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    amount: int
    def __init__(self, amount: _Optional[int] = ...) -> None: ...
