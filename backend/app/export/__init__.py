"""Build the renderer input (the dict biota's /publish route built) from a Publication."""
from ..models import Publication

SPECIES_RANK = 34


def grouped_specimens(item) -> dict[str, list]:
    """{county: [[id, text], ...]} — biota's Item.get_grouped_specimens."""
    grouped: dict[str, list] = {}
    for s in item.specimens:
        if s.display_text:
            grouped.setdefault(s.county or "TBD", []).append([s.id, s.display_text])
    return grouped


def build_export_data(pub: Publication) -> dict:
    data = {
        "title": pub.title,
        "author": pub.author,
        "literatures": [lit.citation for lit in pub.literatures],
        "items": [],
        "item_category": [],
        "keys": [],
    }
    for i in pub.items:
        item = {
            "rank_id": i.rank_id or "",
            "commonNames": i.common_names,
            "description": i.description,
            "distribution": i.distribution,
            "fullScientificName": i.usage_text or "",
            "scientificName": i.scientific_name,
            "note": i.note,
            "synonyms": [s.usage_text for s in i.synonyms],
            "specimens": grouped_specimens(i),
            "images": [
                {"url": im.url, "attribution": im.attribution or "", "caption": im.caption or "",
                 "license": im.license or "", "source": im.source, "link": im.link or ""}
                for im in i.images
            ],
            "source_data": {**(i.source_data or {}), "name_authors": i.name_authors or ""},
        }
        if (i.rank_id or 0) >= SPECIES_RANK:
            data["items"].append(item)
        else:
            data["item_category"].append(item)

    names = {i.id: i.scientific_name for i in pub.items}
    for key in pub.keys:
        data["keys"].append({
            "title": key.title,
            "entries": [{
                "number": e.number,
                "indent_level": e.indent_level,
                "description": e.description,
                "result_couplet": e.result_couplet,
                "result_item_id": e.result_item_id,
                "result_item_name": names.get(e.result_item_id, "") if e.result_item_id else "",
            } for e in key.entries],
        })
    return data
