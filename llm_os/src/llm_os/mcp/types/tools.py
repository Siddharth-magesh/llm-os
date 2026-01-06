"""
MCP Tool Types

Type definitions for MCP tools, parameters, and results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolContentType(str, Enum):
    """Types of content that tools can return."""
    TEXT = "text"
    IMAGE = "image"
    RESOURCE = "resource"
    ERROR = "error"


class ParameterType(str, Enum):
    """JSON Schema parameter types."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None
    items: dict[str, Any] | None = None  # For array types
    properties: dict[str, Any] | None = None  # For object types

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {
            "type": self.type.value,
            "description": self.description,
        }

        if self.default is not None:
            schema["default"] = self.default

        if self.enum:
            schema["enum"] = self.enum

        if self.items:
            schema["items"] = self.items

        if self.properties:
            schema["properties"] = self.properties

        return schema


@dataclass
class ToolContent:
    """Content returned by a tool."""
    type: ToolContentType
    text: str | None = None
    data: bytes | None = None
    mime_type: str | None = None
    uri: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {"type": self.type.value}

        if self.text is not None:
            result["text"] = self.text
        if self.data is not None:
            result["data"] = self.data
        if self.mime_type:
            result["mimeType"] = self.mime_type
        if self.uri:
            result["uri"] = self.uri

        return result

    @classmethod
    def text_content(cls, text: str) -> ToolContent:
        """Create text content."""
        return cls(type=ToolContentType.TEXT, text=text)

    @classmethod
    def error_content(cls, error: str) -> ToolContent:
        """Create error content."""
        return cls(type=ToolContentType.ERROR, text=error)

    @classmethod
    def image_content(cls, data: bytes, mime_type: str = "image/png") -> ToolContent:
        """Create image content."""
        return cls(type=ToolContentType.IMAGE, data=data, mime_type=mime_type)


@dataclass
class ToolResult:
    """Result from executing a tool."""
    success: bool
    content: list[ToolContent]
    is_error: bool = False
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(cls, text: str, **metadata: Any) -> ToolResult:
        """Create a successful text result."""
        return cls(
            success=True,
            content=[ToolContent.text_content(text)],
            metadata=metadata,
        )

    @classmethod
    def error_result(cls, error: str, **metadata: Any) -> ToolResult:
        """Create an error result."""
        return cls(
            success=False,
            content=[ToolContent.error_content(error)],
            is_error=True,
            error_message=error,
            metadata=metadata,
        )

    def get_text(self) -> str:
        """Get combined text content."""
        texts = []
        for content in self.content:
            if content.text:
                texts.append(content.text)
        return "\n".join(texts)


@dataclass
class Tool:
    """Definition of an MCP tool."""
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    server_id: str = ""
    requires_confirmation: bool = False
    permission_level: str = "read"  # read, write, execute, system, dangerous

    def get_input_schema(self) -> dict[str, Any]:
        """Get JSON Schema for input parameters."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def to_llm_format(self) -> dict[str, Any]:
        """Convert to format suitable for LLM tool calling."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.get_input_schema(),
        }

    def validate_arguments(self, arguments: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate arguments against parameter definitions.

        Returns (is_valid, error_message).
        """
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in arguments:
                return False, f"Missing required parameter: {param.name}"

        # Check types (basic validation)
        for param in self.parameters:
            if param.name in arguments:
                value = arguments[param.name]
                if not self._check_type(value, param.type):
                    return False, f"Invalid type for {param.name}: expected {param.type.value}"

                # Check enum values
                if param.enum and value not in param.enum:
                    return False, f"Invalid value for {param.name}: must be one of {param.enum}"

        return True, ""

    def _check_type(self, value: Any, expected: ParameterType) -> bool:
        """Check if value matches expected type."""
        type_checks = {
            ParameterType.STRING: lambda v: isinstance(v, str),
            ParameterType.NUMBER: lambda v: isinstance(v, (int, float)),
            ParameterType.INTEGER: lambda v: isinstance(v, int),
            ParameterType.BOOLEAN: lambda v: isinstance(v, bool),
            ParameterType.ARRAY: lambda v: isinstance(v, list),
            ParameterType.OBJECT: lambda v: isinstance(v, dict),
        }
        check = type_checks.get(expected)
        return check(value) if check else True


@dataclass
class ToolCall:
    """A request to call a tool."""
    id: str
    name: str
    arguments: dict[str, Any]
    server_id: str | None = None

    def __repr__(self) -> str:
        return f"ToolCall(name={self.name!r}, arguments={self.arguments!r})"
