"""Tests for the taxonomy module."""

import json
import unittest
from pathlib import Path

import jsonschema

from shinto.taxonomy import Taxonomy, TaxonomyComplianceError, TaxonomyField

FIXTURES_DIR = Path(__file__).parent / "fixtures"
(FIXTURES_DIR / "generated").mkdir(exist_ok=True)

TEST_TAXONOMY = json.loads((FIXTURES_DIR / "taxonomy_tilburg_modified_test.json").read_text())
TEST_TAXONOMY_INVALID = json.loads((FIXTURES_DIR / "taxonomy_tilburg_test.json").read_text())
TEST_PROJECT_DATA_LIST = json.loads(
    (FIXTURES_DIR / "project_data_list_tilburg_test.json").read_text()
)


class TestTaxonomy(unittest.TestCase):
    """Test the taxonomy module."""

    def test_valid_number_field(self):
        """Test validation of valid number fields."""
        taxonomy = Taxonomy({"fields": [{"field": "count", "type": "number", "label": "Count"}]})

        # Valid number
        taxonomy.validate_data({"count": 42})
        taxonomy.validate_data({"count": 0})
        taxonomy.validate_data({"count": -10})

    def test_valid_text_field(self):
        """Test validation of valid text fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {"field": "name", "type": "text", "label": "Name"},
                    {"field": "description", "type": "string", "label": "Description"},
                ]
            }
        )

        taxonomy.validate_data({"name": "Project A", "description": "A test project"})
        taxonomy.validate_data({"name": "", "description": ""})

    def test_valid_categorical_field(self):
        """Test validation of valid categorical fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "status",
                        "type": "categorical",
                        "label": "Status",
                        "values": [
                            {"value": "active", "label": "Active"},
                            {"value": "inactive", "label": "Inactive"},
                        ],
                    }
                ]
            }
        )

        taxonomy.validate_data({"status": "active"})
        taxonomy.validate_data({"status": "inactive"})

    def test_valid_multi_categorical_field(self):
        """Test validation of valid multi-categorical fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "tags",
                        "type": "multi_categorical",
                        "label": "Tags",
                        "values": [
                            {"value": "urgent", "label": "Urgent"},
                            {"value": "important", "label": "Important"},
                            {"value": "review", "label": "Review"},
                        ],
                    }
                ]
            }
        )

        taxonomy.validate_data({"tags": ["urgent"]})
        taxonomy.validate_data({"tags": ["urgent", "important"]})
        taxonomy.validate_data({"tags": []})

    def test_valid_datetime_field(self):
        """Test validation of valid date-time fields."""
        taxonomy = Taxonomy(
            {"fields": [{"field": "created_at", "type": "date-time", "label": "Created At"}]}
        )

        taxonomy.validate_data({"created_at": "2025-08-07T00:00:00"})
        taxonomy.validate_data({"created_at": "2025-08-07T00:00:00.000"})
        taxonomy.validate_data({"created_at": "2025-08-07T14:30:45"})
        taxonomy.validate_data({"created_at": "2025-08-07T14:30:45.123456"})

    def test_valid_polygon_field(self):
        """Test validation of valid polygon fields."""
        taxonomy = Taxonomy({"fields": [{"field": "geo", "type": "polygon", "label": "Geometry"}]})

        valid_geojson = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
                "properties": {},
            }
        ]
        taxonomy.validate_data({"geo": valid_geojson})

    def test_invalid_number_field(self):
        """Test validation of invalid number fields."""
        taxonomy = Taxonomy({"fields": [{"field": "count", "type": "number", "label": "Count"}]})

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate_data({"count": "42"})

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate_data({"count": 3.14})

    def test_invalid_categorical_field(self):
        """Test validation of invalid categorical fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "status",
                        "type": "categorical",
                        "label": "Status",
                        "values": [
                            {"value": "active", "label": "Active"},
                            {"value": "inactive", "label": "Inactive"},
                        ],
                    }
                ]
            }
        )

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate_data({"status": "pending"})

    def test_invalid_multi_categorical_field(self):
        """Test validation of invalid multi-categorical fields."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {
                        "field": "tags",
                        "type": "multi_categorical",
                        "label": "Tags",
                        "values": [
                            {"value": "urgent", "label": "Urgent"},
                            {"value": "important", "label": "Important"},
                        ],
                    }
                ]
            }
        )

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate_data({"tags": ["urgent", "invalid"]})

    def test_invalid_datetime_field(self):
        """Test validation of invalid date-time fields."""
        taxonomy = Taxonomy(
            {"fields": [{"field": "created_at", "type": "date-time", "label": "Created At"}]}
        )

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate_data({"created_at": "not-a-date"})

        with self.assertRaises(TaxonomyComplianceError):
            taxonomy.validate_data({"created_at": "2025-13-45"})

    def test_missing_optional_fields(self):
        """Test that missing fields are handled correctly."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {"field": "name", "type": "text", "label": "Name"},
                    {"field": "count", "type": "number", "label": "Count"},
                ]
            }
        )

        # Fields not in data should not raise errors (they're optional)
        taxonomy.validate_data({"name": "Test"})
        taxonomy.validate_data({"count": 5})
        taxonomy.validate_data({})

    def test_complex_valid_data(self):
        """Test validation of complex valid data structures."""
        taxonomy = Taxonomy(
            {
                "fields": [
                    {"field": "project_name", "type": "text", "label": "Project Name"},
                    {"field": "budget", "type": "number", "label": "Budget"},
                    {
                        "field": "status",
                        "type": "categorical",
                        "label": "Status",
                        "values": [
                            {"value": "planning", "label": "Planning"},
                            {"value": "active", "label": "Active"},
                            {"value": "completed", "label": "Completed"},
                        ],
                    },
                    {
                        "field": "features",
                        "type": "multi_categorical",
                        "label": "Features",
                        "values": [
                            {"value": "solar", "label": "Solar Panels"},
                            {"value": "parking", "label": "Parking"},
                            {"value": "garden", "label": "Garden"},
                        ],
                    },
                    {"field": "start_date", "type": "date-time", "label": "Start Date"},
                ]
            }
        )

        valid_data = {
            "project_name": "Green Building Project",
            "budget": 1500000,
            "status": "active",
            "features": ["solar", "garden"],
            "start_date": "2025-01-15T09:00:00",
        }

        taxonomy.validate_data(valid_data)

    def test_taxonomy_creation_real_schema(self):
        """Test the creation of a Taxonomy object."""
        taxonomy = Taxonomy(TEST_TAXONOMY)
        self.assertIsInstance(taxonomy, Taxonomy)
        self.assertIsInstance(taxonomy.fields, list)
        for field in taxonomy.fields:
            self.assertIsInstance(field, TaxonomyField)

    def test_taxonomy_validation_real_data(self):
        """Test the check_taxonomy_compliance function."""
        taxonomy = Taxonomy(TEST_TAXONOMY)

        for item in TEST_PROJECT_DATA_LIST:
            taxonomy.validate_data(item)

    def test_taxonomy_json_schema_real_schema(self):
        """Test the JSON schema generation of a Taxonomy object."""
        taxonomy = Taxonomy(TEST_TAXONOMY)
        json_schema = taxonomy.__to_json_schema__()
        self.assertIsInstance(json_schema, dict)
        (FIXTURES_DIR / "generated/taxonomy_schema.json").write_text(
            json.dumps(json_schema, indent=2)
        )

        jsonschema.validate(
            instance=TEST_PROJECT_DATA_LIST,
            schema={
                "type": "array",
                "items": json_schema,
                "definitions": json_schema.get("definitions", {}),
            },
        )

    def test_taxonomy_invalid_real_schema(self):
        """Test that invalid data raises errors."""
        taxonomy = Taxonomy(TEST_TAXONOMY_INVALID, strict=False)
        taxonomy.__to_json_schema__()

        with self.assertRaises(TaxonomyComplianceError):
            for item in TEST_PROJECT_DATA_LIST:
                taxonomy.validate_data(item)


if __name__ == "__main__":
    unittest.main()
