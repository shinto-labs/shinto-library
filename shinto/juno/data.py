"""Transforms between projects_data and stage_data structures."""

from __future__ import annotations

import logging
from typing import Any


def projects_to_stage_data(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform projects_data to stage_data.

    Stage_data is a list of stages,each stage is a dict with stage info
    and a list of projects in that stage.
    """
    projects_data = []
    for project in projects:
        # add id and timestamp to project data
        project_data = project.get("data", {})
        project_data["_metadata"] = {k: v for k, v in project.items() if k != "data"}
        projects_data.append(project_data)

    stage_data = []
    for project in projects_data:
        for stage in project.get("stages", []):
            stage_info = stage.copy()
            # Project level data takes precedence over stage level data, but log a warning
            # if there is a conflict, also omit stages key from project data when merging
            # to stage data to avoid confusion
            for project_key, project_value in project.items():
                if project_key == "stages":
                    continue
                if project_key in stage_info and stage_info[project_key] != project_value:
                    logging.warning(
                        f"Key {project_key} in project data conflicts with stage data. Project data will take precedence.(stage value: {stage_info[project_key]}, project value: {project_value})"
                    )

                stage_info[project_key] = project_value
            stage_data.append(stage_info)
    return stage_data


def stage_data_to_projects(
    stage_data: list[dict[str, Any]], taxonomy: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Transform stage_data back to projects_data.

    stage_data_to_projects takes stage_data and taxonomy as input
    and reconstructs the original projects_data structure.
    """
    # Build field level mapping from taxonomy
    field_level_map = {}
    if taxonomy and "fields" in taxonomy:
        for field_def in taxonomy["fields"]:
            field_name = field_def.get("field")
            level = field_def.get("level", "stage")  # Default to stage if not specified
            field_level_map[field_name] = level

    projects_dict = {}
    for stage in stage_data:
        # Extract project_id from _metadata
        metadata = stage.get("_metadata", {})
        project_id = metadata.get("id")

        if project_id not in projects_dict:
            # Initialize project with metadata
            projects_dict[project_id] = {
                "id": project_id,
                "timestamp": metadata.get("timestamp"),
                "data": {},
            }
            # Copy other metadata fields to the project level
            for meta_key, meta_value in metadata.items():
                if meta_key not in ["id", "timestamp"]:
                    projects_dict[project_id][meta_key] = meta_value

        project_data = projects_dict[project_id]["data"]

        # Create a new stage dict for this stage's fields
        stage_dict = {}

        for key, value in stage.items():
            if key not in ["_metadata"]:
                # Check if field has a defined level in taxonomy
                level = field_level_map.get(key, "stage")  # Default to stage if not in taxonomy

                if level == "stage":
                    # Add to stage dict
                    stage_dict[key] = value
                elif level == "project":
                    # Add to project data (only once, from first stage)
                    if key not in project_data:
                        project_data[key] = value
                    elif project_data[key] != value:
                        logging.warning(
                            f"Conflict for project-level field {key} in project {project_id}. Using first occurrence."
                        )

        # Add the stage to the stages array (only if there are stage fields)
        if stage_dict:
            if "stages" not in project_data:
                project_data["stages"] = []
            project_data["stages"].append(stage_dict)

    return list(projects_dict.values())
