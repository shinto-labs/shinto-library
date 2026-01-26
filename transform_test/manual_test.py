
import json
from shinto.transform import projects_to_stage_data, transform_stage_data, stage_data_to_projects

def main():
    # Load projects from a sourcefile : example/projects_best.json
    projects = json.load(open("example/projects_best.json"))
    #source_taxonomy = json.load(open("example/taxonomy_best.json"))
    target_taxonomy = json.load(open("example/taxonomy_best_owk.json"))
    transformation = json.load(open("example/transformation_best_owk.json"))

    # Convert projects to flat stage data
    stage_data = projects_to_stage_data(projects)
    print(f"Original: {len(projects)} projects -> {len(stage_data)} stages")

    # Apply transformation
    transformed_stage_data = transform_stage_data(stage_data, transformation)
    print(f"After transformation: {len(transformed_stage_data)} stages")

    # Reconstruct projects using target taxonomy
    reconstructed_projects = stage_data_to_projects(transformed_stage_data, target_taxonomy)
    print(f"Reconstructed: {len(reconstructed_projects)} projects")

    print("\nOriginal Projects Data:")
    print(json.dumps(projects, indent=2))

    print("\nStage Data:")
    print(json.dumps(stage_data, indent=2))

    print("\nTransformed Stage Data:")
    print(json.dumps(transformed_stage_data, indent=2))

    print("\nReconstructed Projects Data:")
    print(json.dumps(reconstructed_projects, indent=2))



if __name__ == "__main__":
    main()
