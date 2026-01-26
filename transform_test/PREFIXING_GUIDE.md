# Field Level Guide for Transform Pipeline

## Overview

The transform pipeline uses prefixes for original fields and explicit "level" configuration for custom fields to make flatten/rebuild operations reversible.

## Field Handling

### During Flatten

`flatten_projects()` defaults to `project_prefix="project_"`:

```python
# Before: project_id, naam, stage_uuid, stage_naam
# After:  project_project_id, project_naam, stage_stage_uuid, stage_stage_naam
```

### During Transformation

**For original fields**: Use prefixed names in paths
**For custom fields**: Use the `"level"` field to specify destination

#### ✅ Correct - With Level Field
```json
{
    "action": "add_field",
    "key": "computed_field",       // Clean name without prefix
    "level": "project",            // Explicit level specification
    "source": {"expr": "..."}
}

{
    "action": "add_field",
    "key": "computed_price",       // Clean name without prefix
    "level": "stage",              // Explicit level specification
    "source": {"expr": "..."}
}
```

#### ❌ Incorrect - Without Level Field
```json
{
    "action": "add_field",
    "key": "computed_field",       // Ambiguous! Will be lost during rebuild
    "source": {"expr": "..."}
}
```

### During Rebuild

`rebuild_projects()` processes fields by prefix and level encoding:

| Field Type | Destination | Example |
|------------|-------------|---------|
| `project_*` | Project dict (prefix stripped) | `project_naam` → `naam` |
| `stage_*` | Stage dict (prefix stripped) | `stage_uuid` → `uuid` |
| `level=project` | Project dict (no prefix) | `label` → `label` |
| `level=stage` | Stage dict (no prefix) | `computed_price` → `computed_price` |

## Example Workflow

### 1. Flatten
```python
projects = [{"project_id": 1, "naam": "Project A", "stages": [...]}]
rows = flatten_projects(projects)
# Result: {"project_project_id": 1, "project_naam": "Project A", "stage_...": ...}
```

### 2. Transform with Level Field
```python
pipeline = [{
    "transformations": [
        {
            "action": "add_field",
            "key": "label",                    # Clean name, no prefix
            "level": "project",                # Explicit level
            "source": {"template": "{project_naam} - {stage_stage_naam}"}
        },
        {
            "action": "add_field",
            "key": "computed_price",           # Clean name, no prefix
            "level": "stage",                  # Explicit level
            "source": {"expr": "stage_price * 1.21"}
        }
    ]
}]
out = run_pipeline(rows, pipeline)
# Fields are internally encoded: __level_project__label, __level_stage__computed_price
```

### 3. Rebuild
```python
projects = rebuild_projects(out, project_id_key="project_project_id")
# Result: {
#   "project_id": 1,
#   "naam": "Project A",
#   "label": "Project A - Stage 1",     # Custom field (decoded from __level_project__)
#   "stages": [
#     {"stage_naam": "Stage 1", "computed_price": 121, ...}
#   ]
# }
```

## Best Practices

1. **Always specify "level" for custom fields** during transformations
2. **Use `level: "project"`** for fields that should appear once per project
3. **Use `level: "stage"`** for fields that vary per stage
4. **Keep original field prefixes** in path references (`project_naam`, not `naam`)
5. **Use clean names** for custom fields (no prefixes in the "key")
6. **In filters/expressions**: Use encoded names for custom fields (`__level_project__fieldname`)

## Internal Encoding

Custom fields are internally encoded during transformation:
- `{"key": "label", "level": "project"}` → stored as `__level_project__label`
- `{"key": "price", "level": "stage"}` → stored as `__level_stage__price`

This encoding is transparent during rebuild—the decoded clean names appear in output.

## Migration from Old Code

If you have existing pipelines:

```python
# Old approach (prefix in key name)
{
    "action": "add_field",
    "key": "project_computed_field",
    "source": {"expr": "..."}
}

# New approach (clean key + level)
{
    "action": "add_field",
    "key": "computed_field",
    "level": "project",
    "source": {"expr": "..."}
}
```

Update all custom field definitions to use the "level" field instead of prefixes in the key name.
