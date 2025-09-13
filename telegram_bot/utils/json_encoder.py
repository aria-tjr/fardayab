from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from dataclasses import asdict, is_dataclass


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling complex objects"""
    
    def default(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        
        # Handle dataclasses
        if is_dataclass(obj):
            return asdict(obj)
        
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle numpy types
        if hasattr(obj, 'item'):
            return obj.item()
        
        # Handle lists and tuples
        if isinstance(obj, (list, tuple)):
            return [self.default(item) for item in obj]
        
        # Handle dictionaries
        if isinstance(obj, dict):
            return {key: self.default(value) for key, value in obj.items()}
        
        # Handle objects with __dict__ attribute
        if hasattr(obj, '__dict__'):
            return {key: self.default(value) for key, value in obj.__dict__.items()}
        
        # Fallback to string representation
        return str(obj)


def safe_json_dumps(data: Any, **kwargs) -> str:
    """Safely serialize data to JSON with custom encoder"""
    try:
        return json.dumps(data, cls=CustomJSONEncoder, ensure_ascii=False, **kwargs)
    except Exception as e:
        # If serialization fails, convert to string representation
        return json.dumps({"error": f"Serialization failed: {str(e)}", "data_type": str(type(data))}, ensure_ascii=False)


def safe_json_loads(json_str: str) -> Any:
    """Safely deserialize JSON string"""
    try:
        return json.loads(json_str)
    except Exception as e:
        return {"error": f"Deserialization failed: {str(e)}", "raw_data": json_str}
