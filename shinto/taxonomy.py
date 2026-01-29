"""Module for handling taxonomies."""

from __future__ import annotations

import datetime
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from typing_extensions import Literal

TAXONOMY_LEVEL = Literal["stage_plus"]

FIELD_TYPE = Literal[
    "number",
    "categorical",
    "text",
    "string",
    "multi_categorical",
    "date-time",
    "polygon",
]

type_mapping = {
    "number": int,
    "text": str,
    "string": str,
    "date-time": str,
    "categorical": str,
    "multi_categorical": list,
    "polygon": list,
}


@lru_cache(maxsize=1)
def _get_geojson_geometry_schema() -> dict:
    """Lazy load the GeoJSON feature schema."""
    return json.loads(
        (Path(__file__).parent / "json_schema/geojson_geometry_schema.json").read_text()
    )


class TaxonomyComplianceError(Exception):
    """Exception raised for data that does not comply with the taxonomy."""


class TaxonomyCategoricalValue:
    """Class representing a value in a taxonomy field."""

    value: str
    label: str | None
    description: str | None

    def __init__(self, value_dict: dict):
        """Initialize the TaxonomyCategoricalValue from a dictionary."""
        if not isinstance(value_dict, dict):
            raise TypeError("value_dict must be a dictionary.")
        if "value" not in value_dict:
            raise TypeError("value_dict must contain a 'value' key.")
        self.value = value_dict["value"]
        self.label = value_dict.get("label")
        self.description = value_dict.get("description")


class TaxonomyField:
    """Class representing a field in a taxonomy."""

    field_id: str
    type: FIELD_TYPE
    label: str
    values: list[TaxonomyCategoricalValue] | None
    description: str | None
    tags: list[str] | None

    def __init__(self, field_dict: dict, strict: bool = True):
        """
        Initialize the TaxonomyField from a dictionary.

        Raises:
            TypeError: If field_dict is not valid
            ValueError: If field_dict is missing required fields

        """
        if not isinstance(field_dict, dict):
            raise TypeError("field_dict must be a dictionary.")
        if "field" not in field_dict or "type" not in field_dict or "label" not in field_dict:
            raise TypeError("field_dict must contain 'field', 'type', and 'label' keys.")
        if field_dict["type"] not in FIELD_TYPE.__args__:
            raise TypeError(
                f"Unrecognized field type: {field_dict['type']}."
                f"Must be one of {FIELD_TYPE.__args__}."
            )
        self.field_id = field_dict["field"]
        self.type = field_dict["type"]
        self.label = field_dict["label"]
        self.description = field_dict.get("description")
        self.tags = field_dict.get("tags")
        self.values = None
        if "values" in field_dict:
            if not isinstance(field_dict["values"], list):
                raise TypeError("field_dict['values'] must be a list.")
            self.values = [TaxonomyCategoricalValue(v) for v in field_dict["values"]]
        if self.type in ["categorical", "multi_categorical"] and not self.values and strict:
            raise ValueError(
                f"Field of type '{self.type}' must have 'values' defined '{self.field_id}'."
            )

    def __to_json_schema__(self) -> dict:
        """Build the JSON schema definition for this field."""
        field_schema: dict = {"title": self.label, "type": None}

        if self.description:
            field_schema["description"] = self.description

        if self.type == "number":
            field_schema["type"] = "integer"
        elif self.type in ["text", "string"]:
            field_schema["type"] = "string"
        elif self.type == "date-time":
            field_schema["type"] = "string"
            field_schema["format"] = "date-time"
        elif self.type == "categorical":
            field_schema["type"] = "string"
            if self.values:
                field_schema["enum"] = [val.value for val in self.values]
        elif self.type == "multi_categorical":
            field_schema["type"] = "array"
            field_schema["items"] = {"type": "string"}
            if self.values:
                field_schema["items"]["enum"] = [val.value for val in self.values]
        elif self.type == "polygon":
            field_schema = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"geometry": {"$ref": "#/definitions/geojson_geometry"}},
                    "required": ["geometry"],
                },
                "description": "A list of GeoJSON features representing polygons.",
            }

        if self.type in ("multi_categorical", "categorical") and self.values:
            value_desc = self._build_json_schema_values_description()
            if value_desc:
                field_schema["description"] = (
                    field_schema.get("description", "") + value_desc
                ).strip()

        return field_schema

    def _build_json_schema_values_description(self) -> str:
        """Generate a description of possible values for categorical fields."""
        value_docs = []
        for val in self.values:
            if val.label or val.description:
                parts = [f"'{val.value}'"]
                if val.label:
                    parts.append(val.label)
                if val.description:
                    parts.append(f"({val.description})")
                value_docs.append(" - ".join(parts))
        if value_docs:
            return "\nPossible values:\n- " + "\n- ".join(value_docs)
        return ""

    def validate(self, value: Any):  # noqa: ANN401
        """
        Validate a single field value against its type and constraints.

        Args:
            value: The value to validate

        Raises:
            TaxonomyComplianceError: If value doesn't comply

        """
        # TODO: Should we enforce required fields?
        # https://shintolabs.atlassian.net/browse/DOT-755
        if value is None:
            raise TaxonomyComplianceError(f"Field '{self.field_id}' is required but missing.")

        if not isinstance(value, type_mapping[self.type]):
            raise TaxonomyComplianceError(
                f"Field '{self.field_id}' expects type {type_mapping[self.type].__name__}, "
                f"got {type(value).__name__}: {value}"
            )

        if self.type == "multi_categorical":
            self._validate_multi_categorical(value)
        elif self.type == "categorical":
            self._validate_categorical(value)
        elif self.type == "date-time":
            self._validate_date_time(value)

        if self.type == "polygon":
            self._validate_polygon(value)

    def _validate_multi_categorical(self, value: Any):  # noqa: ANN401
        """Validate multi_categorical field value."""
        for v in value:
            if v not in [val.value for val in self.values]:
                raise TaxonomyComplianceError(
                    f"Field '{self.field_id}' has invalid value '{v}'. "
                    f"Allowed values are {[val.value for val in self.values]}"
                )

    def _validate_categorical(self, value: Any):  # noqa: ANN401
        """Validate categorical field value."""
        if value not in [val.value for val in self.values]:
            raise TaxonomyComplianceError(
                f"Field '{self.field_id}' has invalid value '{value}'. "
                f"Allowed values are {[val.value for val in self.values]}"
            )

    def _validate_date_time(self, value: Any):  # noqa: ANN401
        """Validate date-time field value."""
        try:
            datetime.datetime.fromisoformat(value)
        except ValueError as e:
            raise TaxonomyComplianceError(
                f"Field '{self.field_id}' expects a date-time in ISO 8601 format, got: {value}"
            ) from e

    def _validate_polygon(self, value: Any):  # noqa: ANN401
        """Validate polygon field value."""
        # TODO: Is polygon always a list of GeoJSON features?
        # https://shintolabs.atlassian.net/browse/DOT-755
        try:
            for item in value:
                if "geometry" not in item:
                    raise TaxonomyComplianceError(
                        f"Field '{self.field_id}' contains invalid GeoJSON polygon: {value}"
                    )
                validate(item["geometry"], _get_geojson_geometry_schema())
        except ValidationError as e:
            raise TaxonomyComplianceError(
                f"Field '{self.field_id}' contains invalid GeoJSON polygon: {value}"
            ) from e


class Taxonomy:
    """Class representing a taxonomy."""

    level: TAXONOMY_LEVEL | None
    fields: list[TaxonomyField]

    def __init__(self, taxonomy_dict: dict, strict: bool = True):
        """
        Initialize the Taxonomy from a dictionary.

        Raises:
            TypeError: If taxonomy_dict is not valid
            ValueError: If taxonomy_dict is missing required fields

        """
        if not isinstance(taxonomy_dict, dict):
            raise TypeError("taxonomy_dict must be a dictionary.")
        if "fields" not in taxonomy_dict:
            raise TypeError("taxonomy_dict must contain a 'fields' key.")
        if not isinstance(taxonomy_dict["fields"], list):
            raise TypeError("taxonomy_dict['fields'] must be a list.")
        if len(taxonomy_dict["fields"]) == 0:
            raise ValueError("taxonomy_dict['fields'] must contain at least one field.")
        self.level = taxonomy_dict.get("level")
        self.fields = [TaxonomyField(field_dict, strict) for field_dict in taxonomy_dict["fields"]]

    def validate_data(self, data: dict):
        """
        Validate data against the taxonomy.

        Args:
            data: Project data dictionary (with potential 'stages' array)

        Raises:
            TaxonomyComplianceError: If value doesn't comply

        """
        for field in self.fields:
            # TODO: Or are fields always required?
            # https://shintolabs.atlassian.net/browse/DOT-755
            if field.field_id in data:
                field.validate(data[field.field_id])

            if "stages" in data:
                for idx, stage in enumerate(data["stages"]):
                    if field.field_id in stage:
                        try:
                            field.validate(stage[field.field_id])
                        except TaxonomyComplianceError as e:
                            raise TaxonomyComplianceError(
                                f"Failed to validate field '{field.field_id}' in stage {idx} "
                            ) from e

    def __to_json_schema__(self) -> dict:
        """Convert a taxonomy to a JSON schema."""
        # TODO: Are any fields required in the data/schema?
        # https://shintolabs.atlassian.net/browse/DOT-755
        definitions = {
            "taxonomy_field_properties": {
                "type": "object",
                "properties": {field.field_id: field.__to_json_schema__() for field in self.fields},
                "required": [],
            }
        }

        if any(field.type == "polygon" for field in self.fields):
            definitions["geojson_geometry"] = _get_geojson_geometry_schema()

        return {
            "title": "Taxonomy Data Schema",
            "type": "object",
            "allOf": [{"$ref": "#/definitions/taxonomy_field_properties"}],
            "properties": {
                "stages": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/taxonomy_field_properties"},
                }
            },
            "required": [],
            "definitions": definitions,
        }
