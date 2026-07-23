"""Transform project data into a flat format suitable for the 'basisset20' Excel export."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from shinto import transform_data
from shinto.juno import projects_to_stage_data, stage_data_to_projects
from shinto.mimir.data import (
    get_project_list,
    get_project_list_async,
    get_taxonomy_by_name,
    get_taxonomy_by_name_async,
    get_transformation_by_name,
    get_transformation_by_name_async,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from shinto.pg.connection import AsyncConnection


def load_taxonomy_value_to_label_mapping(taxonomy: dict[str, Any]) -> dict[str, dict[Any, str]]:
    """
    Load taxonomy and create a mapping dictionary for each field.

    Returns a dict like: {field_name: {value: label}}
    """
    mapping = {}
    for field in taxonomy.get("fields", []):
        field_name = field.get("field")
        if field_name and "values" in field:
            mapping[field_name] = {}
            for value_info in field["values"]:
                if isinstance(value_info, dict):
                    value = value_info.get("value")
                    label = value_info.get("label")
                    if value is not None and label:
                        mapping[field_name][value] = label

    return mapping


def get_label_or_value(mapping: dict[str, dict[Any, str]], field_name: str, value: Any) -> Any:
    """Get the label for a value, or return the value itself if no label found."""
    if value is None:
        return value
    if field_name in mapping and value in mapping[field_name]:
        return mapping[field_name][value]
    return value


def sum_bruto_aantalwoningen(
    stages: list[dict[str, Any]], colname: str, colvalue: list[Any]
) -> int:
    """Sum the bruto_aantalwoningen for stages where colname is in colvalue."""
    return sum(
        stage.get("bruto_aantalwoningen", 0) for stage in stages if stage.get(colname) in colvalue
    )


def aggregate_samengevoegde_plannen(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate all projects with naam='Samengevoegde plannen' into a single project."""
    samengevoegde = []
    other_projects = []

    for project in data:
        project_data = project.get("data", {})
        naam = project_data.get("naam", "")

        if naam == "Samengevoegde plannen":
            samengevoegde.append(project)
        else:
            other_projects.append(project)

    # If there are projects to aggregate
    if len(samengevoegde) > 1:
        # Use the first project as the base
        aggregated = samengevoegde[0].copy()
        aggregated_data = aggregated["data"]

        # Combine all stages from all samengevoegde projects
        all_stages = []
        for proj in samengevoegde:
            all_stages.extend(proj.get("data", {}).get("stages", []))

        aggregated_data["stages"] = all_stages

        # Return the aggregated project first, then all other projects
        return [aggregated, *other_projects]
    # No aggregation needed
    return data


def _eigendom_filter(prijsklasse_value: str, stages: list[dict]) -> tuple[int, int, int, int]:
    huur_eigendom_corporatie = sum(
        stage.get("bruto_aantalwoningen", 0)
        for stage in stages
        if stage.get("prijsklasse") == prijsklasse_value and stage.get("eigendom") == "corporatie"
    )
    huur_eigendom_markt = sum(
        stage.get("bruto_aantalwoningen", 0)
        for stage in stages
        if stage.get("prijsklasse") == prijsklasse_value
        and stage.get("eigendom") == "markt"
        and not stage.get("instandhoudingsplicht")
    )
    huur_eigendom_markt_inst = sum(
        stage.get("bruto_aantalwoningen", 0)
        for stage in stages
        if stage.get("prijsklasse") == prijsklasse_value
        and stage.get("eigendom") == "markt"
        and stage.get("instandhoudingsplicht")
    )
    huur_eigendom_onbekend = sum(
        stage.get("bruto_aantalwoningen", 0)
        for stage in stages
        if stage.get("prijsklasse") == prijsklasse_value
        and (stage.get("eigendom") is None or stage.get("eigendom") == "Onbekend")
    )
    return (
        huur_eigendom_corporatie,
        huur_eigendom_markt,
        huur_eigendom_markt_inst,
        huur_eigendom_onbekend,
    )


def generate_basisset20_flatdata(  # noqa: PLR0915
    data: list[dict[str, Any]], taxonomy: dict[str, Any]
) -> list[dict[str, Any]]:
    """Generate flat data for the 'basisset20' Excel export."""
    value_to_label = load_taxonomy_value_to_label_mapping(taxonomy)

    # Aggregate 'Samengevoegde plannen' projects
    # data = aggregate_samengevoegde_plannen(data)

    # sort projects alphabetically
    data = sorted(data, key=lambda project: project.get("data", {}).get("naam", ""))

    # Extract relevant fields
    rows = []
    geo_rows = []
    geojson_features = []
    num = 1
    for project in data:
        project_data = project.get("data")
        gemeente_code = project_data.get("gemeente_code")
        naam_gemeente = project_data.get("naam_gemeente")
        geometrie_aanwezig = project_data.get("geometrie_aanwezig", "False")
        naam = project_data.get("naam", "Onbekend")
        planstatus = project_data.get("planstatus")

        # let op; de exp returns string bool!
        if isinstance(geometrie_aanwezig, bool):
            geometrie_aanwezig_nice = "Ja" if geometrie_aanwezig else "Nee"
        elif isinstance(geometrie_aanwezig, str):
            geometrie_aanwezig_nice = "Ja" if geometrie_aanwezig == "True" else "Nee"
        # Check if project should go to 'Gerealiseerd of vervallen' sheet
        # if planstatus and planstatus.lower() in ['vervallen']:
        #     plancode = f"{gemeente_code}G{num_gerealiseerd:05d}"
        #     gerealiseerd_vervallen_rows.append({
        #         'gemeente': naam_gemeente,
        #         'status': planstatus,
        #         'plannaam': naam,
        #         'plannummer': plancode,
        #         'locatie': geometrie_aanwezig_nice
        #     })
        #     num_gerealiseerd += 1
        #     continue  # Skip to next project, don't add to main sheet

        plancode = f"{gemeente_code}"

        vertrouwelijk = project_data.get("vertrouwelijk", False)
        vertrouwelijk_nice = "Ja" if vertrouwelijk else "Nee"

        plantype = project_data.get("plantype")
        planologische_status = project_data.get("planologische_status")

        # Translate values to labels using taxonomy
        plantype_label = get_label_or_value(value_to_label, "plantype", plantype)
        planstatus_label = get_label_or_value(value_to_label, "planstatus", planstatus)
        planologische_status_label = planologische_status
        # not used: get_label_or_value(value_to_label, 'planologische_status', planologische_status)

        # Extract geometry data
        geo_data = project_data.get("geo", [])
        point_coords = None
        polygon_geojson = None
        point_geometry = None
        polygon_geometry = None

        for geo_item in geo_data:
            geometry = geo_item.get("geometry", {})
            geo_type = geometry.get("type")
            coords = geometry.get("coordinates")

            if geo_type == "Point" and coords:
                point_coords = f"{coords[1]}, {coords[0]}"
                point_geometry = {"type": "Point", "coordinates": coords}
            elif geo_type == "Polygon" and coords:
                # Format as GeoJSON for mapshaper
                polygon_geojson = json.dumps(
                    {"type": "Polygon", "coordinates": coords}, ensure_ascii=False
                )
                polygon_geometry = {"type": "Polygon", "coordinates": coords}

        # Add row to geography sheet
        if point_coords or polygon_geojson:
            geo_rows.append(
                {
                    "plancode": plancode,
                    "point": point_coords or "",
                    "polygon": polygon_geojson or "",
                }
            )

            # Add features to GeoJSON
            if point_geometry:
                geojson_features.append(
                    {
                        "type": "Feature",
                        "properties": {"plancode": plancode, "type": "point"},
                        "geometry": point_geometry,
                    }
                )
            if polygon_geometry:
                geojson_features.append(
                    {
                        "type": "Feature",
                        "properties": {"plancode": plancode, "type": "polygon"},
                        "geometry": polygon_geometry,
                    }
                )

        # Calculate stage counts
        stages = project_data.get("stages", [])
        bruto = sum(stage.get("bruto_aantalwoningen", 0) for stage in stages)
        sloop = sum(stage.get("sloop_aantalwoningen", 0) for stage in stages)
        opleverjaar_2025 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2025])
        opleverjaar_2026 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2026])
        opleverjaar_2027 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2027])
        opleverjaar_2028 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2028])
        opleverjaar_2029 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2029])
        opleverjaar_2030 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2030])
        opleverjaar_2031 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2031])
        opleverjaar_2032 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2032])
        opleverjaar_2033 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2033])
        opleverjaar_2034 = sum_bruto_aantalwoningen(stages, "opleverjaar", [2034])
        opleverjaar_2035_2039 = sum_bruto_aantalwoningen(
            stages, "opleverjaar", [2035, 2036, 2037, 2038, 2039]
        )
        opleverjaar_2040_2044 = sum_bruto_aantalwoningen(
            stages, "opleverjaar", [2040, 2041, 2042, 2043, 2044]
        )

        woningtype_eengezins = sum_bruto_aantalwoningen(stages, "woningtype", ["eengezinswoningen"])
        woningtype_meergezins = sum_bruto_aantalwoningen(
            stages, "woningtype", ["meergezinswoningen"]
        )
        woningtype_onbekend = sum(
            stage.get("bruto_aantalwoningen", 0)
            for stage in stages
            if stage.get("woningtype") is None or stage.get("woningtype") == "Onbekend"
        )

        (
            huur_sociaal_eigendom_corporatie,
            huur_sociaal_eigendom_markt,
            huur_sociaal_eigendom_markt_inst,
            huur_sociaal_eigendom_onbekend,
        ) = _eigendom_filter("huur_sociaal", stages)
        (
            huur_middelduur_eigendom_corporatie,
            huur_middelduur_eigendom_markt,
            huur_middelduur_eigendom_markt_inst,
            huur_middelduur_eigendom_onbekend,
        ) = _eigendom_filter("huur_middelduur", stages)

        huur_duur = sum_bruto_aantalwoningen(stages, "prijsklasse", ["huur_duur"])
        huur_onbekend = sum(
            stage.get("bruto_aantalwoningen", 0)
            for stage in stages
            if (stage.get("prijsklasse") in [None, "Onbekend"] and stage.get("huur_koop") == "huur")
        )

        koop_betaalbaar = sum_bruto_aantalwoningen(
            stages, "prijsklasse", ["koop_goedkoop", "koop_middelduur"]
        )
        koop_duur = sum_bruto_aantalwoningen(stages, "prijsklasse", ["koop_duur"])
        koop_onbekend = sum(
            stage.get("bruto_aantalwoningen", 0)
            for stage in stages
            if (stage.get("prijsklasse") in [None, "Onbekend"] and stage.get("huur_koop") == "koop")
        )

        prijsklasse_onbekend = sum(
            stage.get("bruto_aantalwoningen", 0)
            for stage in stages
            if (
                stage.get("prijsklasse") in [None, "Onbekend"]
                and stage.get("huur_koop") in [None, "Onbekend"]
            )
        )

        nultredenwoning = sum_bruto_aantalwoningen(
            stages, "wonen_voor_ouderen", ["nultredenwoning"]
        )
        geclusterde_woonvorm = sum_bruto_aantalwoningen(
            stages, "wonen_voor_ouderen", ["geclusterde woonvorm"]
        )
        zorggeschikte_woning = sum_bruto_aantalwoningen(
            stages, "wonen_voor_ouderen", ["zorggeschikte woning"]
        )
        overig_geschikt_voor_ouderen = sum_bruto_aantalwoningen(
            stages, "wonen_voor_ouderen", ["overig geschikt voor ouderen"]
        )

        tijdelijke_woningen = sum_bruto_aantalwoningen(stages, "tijdelijke_woningen", [True])

        rows.append(
            {
                "naam_gemeente": naam_gemeente,
                "vertrouwelijk": vertrouwelijk_nice,
                "naam": naam,
                "plancode": plancode,
                "planstatus": planstatus_label,
                "geometrie_aanwezig": geometrie_aanwezig_nice,
                "sloop_aantalwoningen": sloop,
                "bruto_aantalwoningen": bruto,
                "netto_aantalwoningen": bruto - sloop,
                "opleverjaar_2025": opleverjaar_2025,
                "opleverjaar_2026": opleverjaar_2026,
                "opleverjaar_2027": opleverjaar_2027,
                "opleverjaar_2028": opleverjaar_2028,
                "opleverjaar_2029": opleverjaar_2029,
                "opleverjaar_2030": opleverjaar_2030,
                "opleverjaar_2031": opleverjaar_2031,
                "opleverjaar_2032": opleverjaar_2032,
                "opleverjaar_2033": opleverjaar_2033,
                "opleverjaar_2034": opleverjaar_2034,
                "opleverjaar_2035_2039": opleverjaar_2035_2039,
                "opleverjaar_2040_2044": opleverjaar_2040_2044,
                "c1": bruto
                - opleverjaar_2025
                - opleverjaar_2026
                - opleverjaar_2027
                - opleverjaar_2028
                - opleverjaar_2029
                - opleverjaar_2030
                - opleverjaar_2031
                - opleverjaar_2032
                - opleverjaar_2033
                - opleverjaar_2034
                - opleverjaar_2035_2039
                - opleverjaar_2040_2044,
                "plantype": plantype_label,
                "planologische_status": planologische_status_label,
                "tijdelijke_woningen": tijdelijke_woningen,
                "woningtype_eengezins": woningtype_eengezins,
                "woningtype_meergezins": woningtype_meergezins,
                "woningtype_onbekend": woningtype_onbekend,
                "c2": bruto - woningtype_eengezins - woningtype_meergezins - woningtype_onbekend,
                "c3": nultredenwoning
                + geclusterde_woonvorm
                + zorggeschikte_woning
                + overig_geschikt_voor_ouderen,
                "nultredenwoning": nultredenwoning,
                "geclusterde_woonvorm": geclusterde_woonvorm,
                "zorggeschikte_woning": zorggeschikte_woning,
                "overig_geschikt_voor_ouderen": overig_geschikt_voor_ouderen,
                "huur_sociaal_eigendom_corporatie": huur_sociaal_eigendom_corporatie,
                "huur_sociaal_eigendom_markt": huur_sociaal_eigendom_markt,
                "huur_sociaal_eigendom_markt_inst": huur_sociaal_eigendom_markt_inst,
                "huur_sociaal_eigendom_onbekend": huur_sociaal_eigendom_onbekend,
                "huur_middelduur_eigendom_corporatie": huur_middelduur_eigendom_corporatie,
                "huur_middelduur_eigendom_markt": huur_middelduur_eigendom_markt,
                "huur_middelduur_eigendom_markt_inst": huur_middelduur_eigendom_markt_inst,
                "huur_middelduur_eigendom_onbekend": huur_middelduur_eigendom_onbekend,
                "huur_duur": huur_duur,
                "huur_onbekend": huur_onbekend,
                "koop_betaalbaar": koop_betaalbaar,
                "koop_duur": koop_duur,
                "koop_onbekend": koop_onbekend,
                "prijsklasse_onbekend": prijsklasse_onbekend,
                "c4": bruto
                - huur_sociaal_eigendom_corporatie
                - huur_sociaal_eigendom_markt
                - huur_sociaal_eigendom_markt_inst
                - huur_sociaal_eigendom_onbekend
                - huur_middelduur_eigendom_corporatie
                - huur_middelduur_eigendom_markt
                - huur_middelduur_eigendom_markt_inst
                - huur_middelduur_eigendom_onbekend
                - huur_duur
                - huur_onbekend
                - koop_betaalbaar
                - koop_duur
                - koop_onbekend
                - prijsklasse_onbekend,
            }
        )
        num += 1

    return rows


def get_basisset20_flatdata(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None
) -> dict:
    """Transform data using a project and transformation dictionary."""
    transformation = get_transformation_by_name(connection, action_by, "bassiset20", timestamp)

    taxonomy = get_taxonomy_by_name(connection, action_by, "bassiset20", timestamp)

    projects = get_project_list(connection, action_by, timestamp)

    new_project_data = stage_data_to_projects(
        transform_data(projects_to_stage_data(projects), transformation), taxonomy
    )

    return generate_basisset20_flatdata(new_project_data, taxonomy)


async def get_basisset20_flatdata_async(
    connection: AsyncConnection, action_by: UUID, timestamp: datetime | str | None
) -> dict:
    """Transform data using a project and transformation dictionary."""
    transformation = await get_transformation_by_name_async(
        connection, action_by, "bassiset20", timestamp
    )

    taxonomy = await get_taxonomy_by_name_async(connection, action_by, "bassiset20", timestamp)

    projects = await get_project_list_async(connection, action_by, timestamp)

    new_project_data = stage_data_to_projects(
        transform_data(projects_to_stage_data(projects), transformation), taxonomy
    )

    return generate_basisset20_flatdata(new_project_data, taxonomy)
