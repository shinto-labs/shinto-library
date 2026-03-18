"""Module for handling taxonomies."""

from __future__ import annotations

import datetime
import json
import logging
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
    "date",
    "polygon",
    "object",
    "boolean",
]

type_mapping = {
    "number": int,
    "text": str,
    "string": str,
    "date-time": str,
    "date": str,
    "categorical": str,
    "multi_categorical": list,
    "polygon": list,
    "object": dict,
    "boolean": bool,
}
jsonschema_type_mapping = {
    "number": "integer",
    "text": "string",
    "string": "string",
    "date-time": "string",
    "date": "string",
    "categorical": "string",
    "multi_categorical": "array",
    "polygon": "array",
    "object": "object",
    "boolean": "boolean",
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
    level: str | None

    def __init__(self, field_dict: dict):
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
        # TODO: Converting "info_from_point" to "object" type for now
        # This is a hack until it is fixed in the taxonomy
        # https://shintolabs.atlassian.net/browse/DOT-755
        if self.field_id == "info_from_point":
            self.type = "object"
        self.label = field_dict["label"]
        self.description = field_dict.get("description")
        self.tags = field_dict.get("tags")
        self.values = None
        self.level = field_dict.get("level")
        if "values" in field_dict:
            if self.type not in ("categorical", "multi_categorical"):
                raise TypeError("Only categorical and multi_categorical fields can have 'values'.")
            if not isinstance(field_dict["values"], list):
                raise TypeError("field_dict['values'] must be a list.")
            self.values = [TaxonomyCategoricalValue(v) for v in field_dict["values"]]
        # TODO: we should probably throw an error here.
        # This is a hack until it is fixed in the taxonomy
        # https://shintolabs.atlassian.net/browse/DOT-755
        if self.type in ["categorical", "multi_categorical"] and not self.values:
            self.type = "string"
            logging.warning(
                "Field '%s' is categorical but has no values. Downgrading to string type.",
                self.field_id,
            )

    @property
    def __json_schema__(self) -> dict:
        """Build the JSON schema definition for this field."""
        field_schema: dict = {"title": self.label, "type": None}

        if self.description:
            field_schema["description"] = self.description

        field_schema["type"] = jsonschema_type_mapping[self.type]

        if self.type in ("date-time", "date"):
            field_schema["format"] = "date-time"
        elif self.type in ("categorical", "multi_categorical"):
            if self.values:
                categorical_options = [
                    {
                        "const": val.value,
                        "title": val.label or val.value,
                        **({"description": val.description} if val.description else {}),
                    }
                    for val in self.values
                ]
                if self.type == "categorical":
                    field_schema["oneOf"] = categorical_options
                else:
                    field_schema["items"] = {"type": "string", "oneOf": categorical_options}
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

        return field_schema

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
        elif self.type in ("date-time", "date"):
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

    def __init__(self, taxonomy_dict: dict, skip_unknown_types: bool = False):
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
        if not skip_unknown_types:
            self.fields = [TaxonomyField(field_dict) for field_dict in taxonomy_dict["fields"]]
        else:
            self.fields = []
            for field_dict in taxonomy_dict["fields"]:
                self.try_add_field(field_dict)

    def try_add_field(self, field_dict: dict):
        """Try to add a field to the taxonomy, skipping if the type is unrecognized."""
        try:
            self.fields.append(TaxonomyField(field_dict))
        except TypeError as e:
            field_id = field_dict.get("field", "unknown")
            field_type = field_dict.get("type", "unknown")
            logging.warning(
                "Skipping field '%s' with unrecognized type '%s': %s",
                field_id,
                field_type,
                str(e),
            )

    def validate(self, data: dict):
        """
        Validate data against the taxonomy.

        Args:
            data: Project data dictionary (with potential 'stages' array)

        Raises:
            TaxonomyComplianceError: If value doesn't comply

        """
        for field in self.fields:
            # TODO: Or are fields always required?
            # Also are additional fields allowed in the data that are not defined in the taxonomy?
            # https://shintolabs.atlassian.net/browse/DOT-755
            if field.level == "project":
                if field.field_id in data:
                    field.validate(data[field.field_id])
            else:
                for idx, stage in enumerate(data.get("stages", [])):
                    if field.field_id in stage:
                        try:
                            field.validate(stage[field.field_id])
                        except TaxonomyComplianceError as e:
                            raise TaxonomyComplianceError(
                                f"Failed to validate field '{field.field_id}' in stage {idx} "
                            ) from e

    @property
    def __json_schema__(self) -> dict:
        """Convert a taxonomy to a JSON schema."""
        # TODO: Are any fields required in the data/schema?
        # Also should aditional properties be disallowed?
        # https://shintolabs.atlassian.net/browse/DOT-755
        definitions = {}

        if any(field.type == "polygon" for field in self.fields):
            definitions["geojson_geometry"] = _get_geojson_geometry_schema()

        return {
            "title": "Taxonomy Data Schema",
            "type": "object",
            "properties": {
                **{
                    field.field_id: field.__json_schema__
                    for field in self.fields
                    if field.level == "project"
                },
                "stages": {
                    "title": "Project Stages",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            field.field_id: field.__json_schema__
                            for field in self.fields
                            if not field.level or field.level != "project"
                        },
                    },
                },
            },
            **({"definitions": definitions} if definitions else {}),
        }
