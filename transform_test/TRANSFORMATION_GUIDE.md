# Transformation Configuration Guide

## Overview

The transformation system provides a powerful pipeline-based approach to transform project data. Transformations are defined in JSON configuration files that specify a series of steps to filter, modify, and reshape data.

## File Structure

A transformation configuration is a **JSON array** where each element represents a transformation step. Steps are executed sequentially, with each step receiving the output from the previous step.

```json
[
  {
    "name": "Step 1 description",
    "init": "copy",
    "transformations": [...],
    "filter": {...}
  },
  {
    "name": "Step 2 description",
    "init": "empty",
    "transformations": [...]
  }
]
```

## What is a Taxonomy?

In this transformation system, a **taxonomy** is a schema definition that describes the structure and hierarchy of your project data. It defines which fields belong at the **project level** versus the **stage level**, enabling proper reconstruction of hierarchical project structures after transformation.

### Purpose

The transformation system works with flattened "stage data" - where each row represents a single stage from a project. When reconstructing the original project structure, the taxonomy tells the system how to organize fields back into the proper hierarchy:

- **Project-level fields**: Appear once per project (e.g., project ID, project name, metadata)
- **Stage-level fields**: Appear once per stage within a project (e.g., stage status, stage date, stage-specific details)

### Taxonomy Structure

A taxonomy is a JSON object with a `fields` array:

```json
{
  "fields": [
    {
      "field": "project_name",
      "level": "project"
    },
    {
      "field": "project_description",
      "level": "project"
    },
    {
      "field": "stage_status",
      "level": "stage"
    },
    {
      "field": "stage_date",
      "level": "stage"
    }
  ]
}
```

**Properties:**
- `field` (string): The name of the field
- `level` (string): Either `"project"` or `"stage"`

### How It Works

1. **Flattening**: `projects_to_stage_data()` converts hierarchical projects into flat stage data
   - Each project with multiple stages becomes multiple rows
   - Project-level fields are duplicated across all stage rows

2. **Transformation**: Your transformation pipeline processes the flat stage data
   - Add, remove, rename, or modify fields
   - Filter out unwanted stages

3. **Reconstruction**: `stage_data_to_projects()` uses the taxonomy to rebuild the hierarchy
   - Groups stages back into projects
   - Uses field-level definitions to place fields correctly
   - Project-level fields are extracted from the first stage and placed at the project level
   - Stage-level fields remain within each stage

### Example: Before and After

**Original Project Structure:**
```json
{
  "id": "project-123",
  "data": {
    "project_name": "Road Expansion",
    "project_budget": 1000000,
    "stages": [
      {
        "stage_name": "Planning",
        "stage_status": "complete"
      },
      {
        "stage_name": "Construction",
        "stage_status": "in_progress"
      }
    ]
  }
}
```

**Flattened Stage Data** (2 rows):
```json
[
  {
    "_metadata": {"id": "project-123"},
    "project_name": "Road Expansion",
    "project_budget": 1000000,
    "stage_name": "Planning",
    "stage_status": "complete"
  },
  {
    "_metadata": {"id": "project-123"},
    "project_name": "Road Expansion",
    "project_budget": 1000000,
    "stage_name": "Construction",
    "stage_status": "in_progress"
  }
]
```

**Taxonomy:**
```json
{
  "fields": [
    {"field": "project_name", "level": "project"},
    {"field": "project_budget", "level": "project"},
    {"field": "stage_name", "level": "stage"},
    {"field": "stage_status", "level": "stage"}
  ]
}
```

**Reconstructed Project** (after transformation):
```json
{
  "id": "project-123",
  "data": {
    "project_name": "Road Expansion",
    "project_budget": 1000000,
    "stages": [
      {
        "stage_name": "Planning",
        "stage_status": "complete"
      },
      {
        "stage_name": "Construction",
        "stage_status": "in_progress"
      }
    ]
  }
}
```

### Default Behavior

If a field is **not defined** in the taxonomy:
- It defaults to **stage-level**
- It will be placed within individual stages during reconstruction

### When to Define Taxonomy

You need a taxonomy when:
- Your data has a hierarchical structure (projects containing stages)
- You're transforming data and need to reconstruct it afterward
- You want to ensure fields are placed at the correct level in the output

### Action Field Levels

When using `add_field` or `set_field` actions, you can specify a `level` property:

```json
{
  "action": "add_field",
  "key": "calculated_total",
  "type": "float",
  "level": "project",
  "source": {"expr": "sum(stage_costs)"}
}
```

This `level` property serves as metadata and should align with your taxonomy definition to ensure proper reconstruction.

## Step Structure

Each transformation step is an object with the following properties:

### Required Properties

- **`name`** (string): A descriptive name for the pipeline step

### Optional Properties

- **`init`** (string): Initialization strategy for the output row
  - `"copy"` (default): Start with a copy of the input row
  - `"empty"`: Start with an empty row

- **`transformations`** (array): List of transformation actions to apply (see Actions section)

- **`filter`** (object): Optional filter to apply after transformations. Rows that don't pass are dropped from the output

## Actions

Actions define how to manipulate data fields. They are executed in the order specified within each step's `transformations` array.

### 1. `add_field` - Add a New Field

Adds a field only if it doesn't already exist.

```json
{
  "action": "add_field",
  "key": "field_name",
  "type": "string",
  "level": "stage",
  "source": {...}
}
```

**Properties:**
- `key` (required): Name of the field to add
- `type` (optional): Data type for casting - `"string"`, `"int"`, `"float"`, `"bool"`, `"json"`
- `level` (optional): `"project"` or `"stage"` - affects reconstruction (see taxonomy)
- `source` (optional): Source specification for the field value (see Sources section)

**Example:**
```json
{
  "action": "add_field",
  "key": "full_name",
  "type": "string",
  "source": {
    "template": "{first_name} {last_name}"
  }
}
```

### 2. `set_field` - Set/Update a Field

Sets a field value, overwriting it if it already exists.

```json
{
  "action": "set_field",
  "key": "field_name",
  "type": "int",
  "source": {...}
}
```

**Properties:** Same as `add_field`, but will overwrite existing values

**Example:**
```json
{
  "action": "set_field",
  "key": "status",
  "type": "string",
  "source": {
    "const": "active"
  }
}
```

### 3. `remove_field` - Remove a Field

Removes a field from the output row.

```json
{
  "action": "remove_field",
  "key": "field_name"
}
```

**Properties:**
- `key` (required): Name of the field to remove

**Example:**
```json
{
  "action": "remove_field",
  "key": "internal_notes"
}
```

### 4. `rename_field` - Rename a Field

Renames an existing field.

```json
{
  "action": "rename_field",
  "from": "old_name",
  "to": "new_name"
}
```

**Properties:**
- `from` (required): Source field name
- `to` (required): Target field name

**Example:**
```json
{
  "action": "rename_field",
  "from": "project_naam",
  "to": "project_name"
}
```

### 5. `copy_field` - Copy a Field

Creates a deep copy of a field with a new name.

```json
{
  "action": "copy_field",
  "from": "source_field",
  "to": "target_field"
}
```

**Properties:**
- `from` (required): Source field name to copy from
- `to` (required): Target field name to copy to

**Example:**
```json
{
  "action": "copy_field",
  "from": "original_date",
  "to": "backup_date"
}
```

## Sources

Sources define where field values come from. They are used in `add_field` and `set_field` actions.

### 1. Constant Value - `const`

Provides a static value.

```json
{
  "source": {
    "const": "fixed value"
  }
}
```

**Examples:**
```json
{"const": "active"}
{"const": 42}
{"const": true}
{"const": ["array", "of", "values"]}
{"const": {"key": "value"}}
```

### 2. Field Path - `path`

Extracts a value from an existing field in the row.

```json
{
  "source": {
    "path": "field_name"
  }
}
```

**Example:**
```json
{
  "action": "add_field",
  "key": "backup_status",
  "source": {
    "path": "current_status"
  }
}
```

### 3. String Template - `template`

Formats a string using field values with `{field_name}` placeholders.

```json
{
  "source": {
    "template": "Hello {first_name} {last_name}!"
  }
}
```

**Notes:**
- Missing or null fields are replaced with empty strings
- Uses Python's `str.format()` syntax

**Example:**
```json
{
  "action": "add_field",
  "key": "display_name",
  "source": {
    "template": "{title}: {description} (ID: {id})"
  }
}
```

### 4. Python Expression - `expr`

Evaluates a Python expression with row fields as variables.

```json
{
  "source": {
    "expr": "field1 + field2"
  }
}
```

**Available built-in functions:**
- `len()`, `min()`, `max()`, `sum()`
- `str()`, `int()`, `float()`, `bool()`
- `sorted()`, `any()`, `all()`

**Examples:**
```json
{"expr": "price * quantity"}
{"expr": "len(items) > 0"}
{"expr": "'active' if status == 1 else 'inactive'"}
{"expr": "max(score1, score2, score3)"}
```

## Filters

Filters determine which rows pass through to the next step. Rows that don't match the filter criteria are dropped.

### 1. Python Expression - `expr`

Evaluates a boolean Python expression.

```json
{
  "filter": {
    "expr": "status == 'active' and age >= 18"
  }
}
```

**Example:**
```json
{
  "filter": {
    "expr": "vertrouwelijk == 'nee' and share_profile in ['public', 'shared']"
  }
}
```

### 2. Logical AND - `all`

All sub-filters must pass.

```json
{
  "filter": {
    "all": [
      {"expr": "age >= 18"},
      {"expr": "status == 'active'"}
    ]
  }
}
```

### 3. Logical OR - `any`

At least one sub-filter must pass.

```json
{
  "filter": {
    "any": [
      {"expr": "priority == 'high'"},
      {"expr": "urgent == true"}
    ]
  }
}
```

### 4. Logical NOT - `not`

Negates the result of a sub-filter.

```json
{
  "filter": {
    "not": {
      "expr": "status == 'deleted'"
    }
  }
}
```

### 5. Field Existence - `exists`

Checks if a field exists and is not null.

```json
{
  "filter": {
    "exists": {
      "path": "email"
    }
  }
}
```

### 6. Equality Comparison - `eq`

Compares two source values for equality.

```json
{
  "filter": {
    "eq": [
      {"path": "status"},
      {"const": "approved"}
    ]
  }
}
```

### 7. Membership Test - `in`

Checks if a value is contained in a collection.

```json
{
  "filter": {
    "in": [
      {"path": "category"},
      {"const": ["A", "B", "C"]}
    ]
  }
}
```

## Type Casting

The `type` property in `add_field` and `set_field` actions casts values to specific types:

- **`"string"`, `"str"`, `"text"`**: Convert to string
- **`"int"`, `"integer"`**: Convert to integer (null/empty becomes null)
- **`"float"`, `"number"`**: Convert to float (null/empty becomes null)
- **`"bool"`, `"boolean"`**: Convert to boolean
  - True values: `"true"`, `"1"`, `"yes"`, `"y"`, `"ja"`, `"j"`, `"waar"`, `"t"`
  - False values: `"false"`, `"0"`, `"no"`, `"n"`, `"nee"`, `"onwaar"`, `"f"`
- **`"json"`, `"object"`, `"dict"`**: Parse JSON string or return object as-is

## Complete Example

Here's a real-world example that filters and sanitizes project data:

```json
[
  {
    "name": "Filter projects for sharing",
    "init": "copy",
    "transformations": [
      {
        "action": "add_field",
        "key": "include_for_sharing",
        "type": "boolean",
        "source": {
          "expr": "vertrouwelijk == 'nee' and share_profile in ['naam_locatie_en_aantallen', 'full']"
        }
      }
    ],
    "filter": {
      "expr": "include_for_sharing == True"
    }
  },
  {
    "name": "Remove sensitive fields",
    "init": "copy",
    "transformations": [
      {
        "action": "remove_field",
        "key": "vertrouwelijk"
      },
      {
        "action": "remove_field",
        "key": "share_profile"
      },
      {
        "action": "remove_field",
        "key": "internal_notes"
      },
      {
        "action": "remove_field",
        "key": "include_for_sharing"
      }
    ]
  },
  {
    "name": "Add display name",
    "init": "copy",
    "transformations": [
      {
        "action": "add_field",
        "key": "display_name",
        "type": "string",
        "source": {
          "template": "{project_name} - {location}"
        }
      }
    ]
  }
]
```

## Advanced Patterns

### Conditional Field Creation

```json
{
  "action": "add_field",
  "key": "priority_label",
  "type": "string",
  "source": {
    "expr": "'High' if priority > 7 else 'Medium' if priority > 3 else 'Low'"
  }
}
```

### Complex Filtering

```json
{
  "filter": {
    "all": [
      {
        "any": [
          {"expr": "category == 'urgent'"},
          {"expr": "priority >= 8"}
        ]
      },
      {
        "not": {
          "expr": "status == 'cancelled'"
        }
      },
      {
        "exists": {
          "path": "assigned_to"
        }
      }
    ]
  }
}
```

### Multi-Step Data Transformation

```json
[
  {
    "name": "Step 1: Calculate derived fields",
    "init": "copy",
    "transformations": [
      {
        "action": "add_field",
        "key": "total_cost",
        "type": "float",
        "source": {
          "expr": "unit_price * quantity"
        }
      }
    ]
  },
  {
    "name": "Step 2: Filter by cost threshold",
    "init": "copy",
    "filter": {
      "expr": "total_cost > 1000"
    }
  },
  {
    "name": "Step 3: Format for output",
    "init": "copy",
    "transformations": [
      {
        "action": "remove_field",
        "key": "internal_id"
      },
      {
        "action": "rename_field",
        "from": "total_cost",
        "to": "cost_eur"
      }
    ]
  }
]
```

## Best Practices

1. **Use Descriptive Step Names**: Make it clear what each step does
2. **Keep Steps Focused**: Each step should have a single, clear purpose
3. **Order Matters**: Remember that steps execute sequentially
4. **Test Incrementally**: Build and test your transformation step by step
5. **Use `add_field` for Safety**: Use `add_field` when you don't want to overwrite existing data
6. **Document Complex Expressions**: Add comments in your JSON (if your parser supports it) or in separate documentation
7. **Consider Performance**: Complex expressions and filters can impact performance on large datasets
8. **Validate Your Schema**: Use the provided `transformation_schema.json` to validate your configuration

## Usage in Python

```python
from shinto.transform.transform import (
    projects_to_stage_data,
    transform_stage_data,
    stage_data_to_projects
)
import json

# Load your data and configuration
projects = json.load(open("projects.json"))
transformation = json.load(open("transformation.json"))
taxonomy = json.load(open("taxonomy.json"))

# Convert to stage data
stage_data = projects_to_stage_data(projects)

# Apply transformation
transformed = transform_stage_data(stage_data, transformation)

# Reconstruct projects
result = stage_data_to_projects(transformed, taxonomy)
```

## Troubleshooting

### Common Issues

1. **Field Not Found**: Ensure the field exists in the input data before referencing it
2. **Type Casting Errors**: Verify that values can be cast to the specified type
3. **Filter Dropping All Rows**: Check filter expressions are correct and match your data
4. **Expression Evaluation Errors**: Ensure Python expressions use valid syntax and available functions
5. **Template Format Errors**: Make sure field names in templates are spelled correctly

### Debug Tips

- Test each step independently
- Print intermediate results after each transformation step
- Use simple expressions first, then add complexity
- Verify your JSON syntax with a validator
- Check that field references match actual field names (case-sensitive)
