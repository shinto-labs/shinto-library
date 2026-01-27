#!/usr/bin/env python3


import json
from pathlib import Path
from shinto import transform_data
from shinto.juno import projects_to_stage_data, stage_data_to_projects


def generate_owk_projects(projects):
    features = []
    for project_data in projects:
        project = project_data.get("data", {})
        geometry = None
        if "geo" in project and project["geo"] is not None:
             for g in project.get("geo", []):
                  geometry_item = g.get("geometry", {})
                  if geometry_item.get("type") == "Point":
                      geometry = geometry_item.copy()
                      break
        if geometry is None :
            continue

        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "project_id": project.get("project_id"),
                "naam": project.get("naam"),
                "omschrijving": project.get("omschrijving"),
                "flag": ['show_count_stats'],#project.get("flags", []),
                "image": project.get("image"),
                "url": project.get("url"),
                "ontwikkelaar": None, #project.get("ontwikkelaar"),
                "buurt_code": project.get("info_from_point", {}).get("buurt").get("buurt_code"),
                "buurt_naam": project.get("info_from_point", {}).get("buurt").get("buurt_naam"),
                "wijk_code": project.get("info_from_point", {}).get("wijk").get("wijk_code"),
                "wijk_naam": project.get("info_from_point", {}).get("wijk").get("wijk_naam")
            }
        }
        features.append(feature)

    geojson = {
         "type": "FeatureCollection",
         "features": features
    }
    return geojson

def generate_owk_projects_shape(projects):
    features = []
    for project_data in projects:
        project = project_data.get("data", {})
        geometry = None
        if "geo" in project and project["geo"] is not None:
             for g in project.get("geo", []):
                  geometry_item = g.get("geometry", {})
                  if geometry_item.get("type") in ["Polygon", "MultiPolygon"]:
                      geometry = geometry_item.copy()
                      break
        if geometry is None :
            continue

        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "project_id": project.get("project_id")
            }
        }
        features.append(feature)

    geojson = {
         "type": "FeatureCollection",
         "features": features
    }
    return geojson

def generate_owk_projects_stage(projects):
    stages = []
    for project_data in projects:
        project = project_data.get("data", {})
        for stage in project.get("stages", []):
            stage_item = {
                "project_id": project.get("project_id"),
                "stage_id": stage.get("stage_id"),
                "status": stage.get("status"),
                "start_date": stage.get("start_date"),
                "end_date": stage.get("end_date"),
                "aantal_woningen": stage.get("aantal_woningen"),
                "bouwhoogte": stage.get("bouwhoogte"),
                "functie": stage.get("functie"),
            }
            stages.append(stage_item)
    return stages


def generate_owk_dashboard(projects):
    dashboard = []
    for project_data in projects:
        project = project_data.get("data", {})
        stages = project.get("stages", [])
        for stage in stages:
            dashboard_item = {
                "woningtype": stage.get("woningtype"),
                "opleverjaar": stage.get("opleverjaar"),
                "prijsklasse": stage.get("prijsklasse"),
                "huur_koop": "Huur",
                "netto_aantal_woningen": 30,
                "bruto_aantal_woningen": 30,
                "sloop_aantal_woningen": 0,
                "procesfase": "In studie"
            }
            dashboard.append(dashboard_item)
    return dashboard


def order_featurecollection(fc):
    fc["features"] = sorted(fc.get("features", []), key=lambda f: f.get("properties", {}).get("project_id"))
    return fc

def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj



def main():
    # Load projects from a sourcefile : <script-root>/example/projects_best.json
    projects = json.load(open("example/projects_best.json"))
    # print("\nOriginal Projects Data:")
    # print(json.dumps(projects, indent=2))

    #source_taxonomy = json.load(open("example/taxonomy_best.json"))
    target_taxonomy = json.load(open("example/taxonomy_best_owk.json"))


    transformation = json.load(open("example/transformation_best_owk.json"))

    # Convert projects to flat stage data
    stage_data = projects_to_stage_data(projects)
    # print(f"Original: {len(projects)} projects -> {len(stage_data)} stages")
    # print("\nStage Data:")
    # print(json.dumps(stage_data, indent=2))

    # Apply transformation
    transformed_stage_data = transform_data(stage_data, transformation)
    # print(f"After transformation: {len(transformed_stage_data)} stages")
    # print("\nTransformed Stage Data:")
    # print(json.dumps(transformed_stage_data, indent=2))

    # Reconstruct projects using target taxonomy
    reconstructed_projects = stage_data_to_projects(transformed_stage_data, target_taxonomy)
    # print(f"Reconstructed: {len(reconstructed_projects)} projects")
    # print("\nReconstructed Projects Data:")
    # print(json.dumps(reconstructed_projects, indent=2))


    # Making OWK data:
    new_owk_projects = generate_owk_projects(reconstructed_projects)
    # print(f"\nOWK Projects Data:")
    # print(json.dumps(owk_projects, indent=2))

    old_owk_projects = json.load(open("example/best-owk-data//projects.json"))

    if ordered(new_owk_projects) == ordered(old_owk_projects):
        print("OWK Projects data matches expected output.")
    else:
        print("OWK Projects data does NOT match expected output.")

    # write to test1.json and test2.json for diffing
    json.dump(order_featurecollection(new_owk_projects), open("example/best-owk-data/test1.json", "w"), indent=2)
    json.dump(order_featurecollection(old_owk_projects), open("example/best-owk-data/test2.json", "w"), indent=2)


    # owk_projects_shape = generate_owk_projects_shape(reconstructed_projects)
    # # print(f"\nOWK Projects Shape Data:")
    # print(json.dumps(owk_projects_shape, indent=2))

    # owk_projects_stage = generate_owk_projects_stage(reconstructed_projects)
    # # print(f"\nOWK Projects Stage Data:")
    # print(json.dumps(owk_projects_stage, indent=2))

    # owk_projects_stage = generate_owk_dashboard(reconstructed_projects)
    # # print(f"\nOWK Projects Stage Data:")
    # print(json.dumps(owk_projects_stage, indent=2))




if __name__ == "__main__":
    main()
