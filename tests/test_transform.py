#!/usr/bin/env python3
"""Test transformation functionality."""

import pytest
from shinto.transform import transform_data, resolve_source


class TestCoalesce:
    """Test the coalesce source functionality."""

    def test_coalesce_first_value(self):
        """Test that coalesce returns the first non-null, non-empty value."""
        test_data = [
            {
                "id": "1",
                "preferred_name": "Alice",
                "full_name": "Alice Smith",
                "email": "alice@example.com"
            }
        ]

        transformation = [
            {
                "name": "Add contact name using coalesce",
                "init": "copy",
                "transformations": [
                    {
                        "action": "add_field",
                        "key": "contact_name",
                        "type": "string",
                        "source": {
                            "coalesce": ["preferred_name", "full_name", "email"]
                        }
                    }
                ]
            }
        ]

        result = transform_data(test_data, transformation)
        assert result[0]['contact_name'] == "Alice"

    def test_coalesce_skip_empty_string(self):
        """Test that coalesce skips empty strings."""
        test_data = [
            {
                "id": "2",
                "preferred_name": "",
                "full_name": "Bob Jones",
                "email": "bob@example.com"
            }
        ]

        transformation = [
            {
                "name": "Add contact name using coalesce",
                "init": "copy",
                "transformations": [
                    {
                        "action": "add_field",
                        "key": "contact_name",
                        "type": "string",
                        "source": {
                            "coalesce": ["preferred_name", "full_name", "email"]
                        }
                    }
                ]
            }
        ]

        result = transform_data(test_data, transformation)
        assert result[0]['contact_name'] == "Bob Jones"

    def test_coalesce_skip_missing_field(self):
        """Test that coalesce skips missing fields."""
        test_data = [
            {
                "id": "3",
                "full_name": "Charlie Brown",
                "email": "charlie@example.com"
            }
        ]

        transformation = [
            {
                "name": "Add contact name using coalesce",
                "init": "copy",
                "transformations": [
                    {
                        "action": "add_field",
                        "key": "contact_name",
                        "type": "string",
                        "source": {
                            "coalesce": ["preferred_name", "full_name", "email"]
                        }
                    }
                ]
            }
        ]

        result = transform_data(test_data, transformation)
        assert result[0]['contact_name'] == "Charlie Brown"

    def test_coalesce_fallback_to_last(self):
        """Test that coalesce falls back to the last available value."""
        test_data = [
            {
                "id": "4",
                "email": "diana@example.com"
            }
        ]

        transformation = [
            {
                "name": "Add contact name using coalesce",
                "init": "copy",
                "transformations": [
                    {
                        "action": "add_field",
                        "key": "contact_name",
                        "type": "string",
                        "source": {
                            "coalesce": ["preferred_name", "full_name", "email"]
                        }
                    }
                ]
            }
        ]

        result = transform_data(test_data, transformation)
        assert result[0]['contact_name'] == "diana@example.com"

    def test_coalesce_skip_none_values(self):
        """Test that coalesce skips None values."""
        test_data = [
            {
                "id": "5",
                "preferred_name": None,
                "full_name": None,
                "email": "eve@example.com"
            }
        ]

        transformation = [
            {
                "name": "Add contact name using coalesce",
                "init": "copy",
                "transformations": [
                    {
                        "action": "add_field",
                        "key": "contact_name",
                        "type": "string",
                        "source": {
                            "coalesce": ["preferred_name", "full_name", "email"]
                        }
                    }
                ]
            }
        ]

        result = transform_data(test_data, transformation)
        assert result[0]['contact_name'] == "eve@example.com"

    def test_coalesce_all_empty_returns_none(self):
        """Test that coalesce returns None when all fields are empty or missing."""
        test_data = [
            {
                "id": "6",
                "preferred_name": "",
                "full_name": None
            }
        ]

        transformation = [
            {
                "name": "Add contact name using coalesce",
                "init": "copy",
                "transformations": [
                    {
                        "action": "add_field",
                        "key": "contact_name",
                        "type": "string",
                        "source": {
                            "coalesce": ["preferred_name", "full_name", "email"]
                        }
                    }
                ]
            }
        ]

        result = transform_data(test_data, transformation)
        assert result[0]['contact_name'] is None

    def test_coalesce_with_numbers(self):
        """Test that coalesce works with numeric values."""
        test_data = [
            {
                "id": "7",
                "priority_1": 0,  # Should skip 0 as it's falsy but not None or empty string
                "priority_2": 5,
                "priority_3": 10
            }
        ]

        transformation = [
            {
                "name": "Add priority using coalesce",
                "init": "copy",
                "transformations": [
                    {
                        "action": "add_field",
                        "key": "final_priority",
                        "type": "int",
                        "source": {
                            "coalesce": ["priority_1", "priority_2", "priority_3"]
                        }
                    }
                ]
            }
        ]

        result = transform_data(test_data, transformation)
        # 0 is not None and not "", so it should be returned
        assert result[0]['final_priority'] == 0

    def test_resolve_source_coalesce_directly(self):
        """Test resolve_source with coalesce directly."""
        row = {
            "field1": "",
            "field2": None,
            "field3": "value3"
        }

        source = {
            "coalesce": ["field1", "field2", "field3"]
        }

        result = resolve_source(row, source)
        assert result == "value3"

