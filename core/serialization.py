"""Redis data serialization/deserialization strategies."""

import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class JsonSerializer:
    """JSON serializer with support for complex Python types."""

    @staticmethod
    def serialize(obj: Any) -> str:
        """Serialize object to JSON string."""
        return json.dumps(obj, cls=ComplexEncoder)

    @staticmethod
    def deserialize(data: str, model_type: Optional[Type[T]] = None) -> Union[Any, T]:
        """Deserialize JSON string to object."""
        obj = json.loads(data, cls=ComplexDecoder)
        if model_type and issubclass(model_type, BaseModel):
            return model_type.parse_obj(obj)
        return obj


class ComplexEncoder(json.JSONEncoder):
    """JSON encoder with support for complex Python types."""

    def default(self, obj: Any) -> Any:
        """Convert complex types to JSON serializable types."""
        if isinstance(obj, (datetime, UUID)):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, BaseModel):
            return obj.dict()
        return super().default(obj)


class ComplexDecoder(json.JSONDecoder):
    """JSON decoder with support for complex Python types."""

    def __init__(self, *args, **kwargs):
        """Initialize decoder with object hook."""
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj: Dict[str, Any]) -> Any:
        """Convert JSON objects to Python types."""
        # Try to parse datetime strings
        for key, value in obj.items():
            if isinstance(value, str):
                try:
                    # ISO format datetime
                    obj[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    try:
                        # UUID
                        obj[key] = UUID(value)
                    except (ValueError, TypeError):
                        continue
        return obj
