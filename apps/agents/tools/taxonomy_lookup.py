"""TaxonomyLookupTool – searches ISCO-08 occupation table by text similarity."""

from __future__ import annotations

from langchain_core.tools import BaseTool
from loguru import logger
from pydantic import Field

ISCO_08_REFERENCE: list[dict[str, str]] = [
    {"isco_code": "6111", "title": "Field Crop Growers", "description": "Growing field crops such as rice, wheat, maize"},
    {"isco_code": "6112", "title": "Tree and Shrub Crop Growers", "description": "Growing tree and shrub crops"},
    {"isco_code": "6114", "title": "Mixed Crop Growers", "description": "Growing mixed crops"},
    {"isco_code": "6121", "title": "Livestock Farmers", "description": "Breeding and raising livestock"},
    {"isco_code": "6130", "title": "Mixed Crop and Livestock Farmers", "description": "Growing crops and raising livestock"},
    {"isco_code": "5221", "title": "Shopkeepers", "description": "Managing or operating small retail shops"},
    {"isco_code": "5223", "title": "Shop Sales Assistants", "description": "Selling goods in shops and stores"},
    {"isco_code": "5243", "title": "Door-to-Door Salespersons", "description": "Selling goods door-to-door"},
    {"isco_code": "5246", "title": "Food Service Counter Attendants", "description": "Serving food and beverages"},
    {"isco_code": "7411", "title": "Building Electricians", "description": "Installing and maintaining electrical systems"},
    {"isco_code": "7412", "title": "Electrical Mechanics and Fitters", "description": "Fitting, maintaining electrical machinery"},
    {"isco_code": "7233", "title": "Agricultural and Industrial Machinery Mechanics", "description": "Maintaining and repairing machinery"},
    {"isco_code": "7231", "title": "Motor Vehicle Mechanics and Repairers", "description": "Repairing motor vehicles"},
    {"isco_code": "7115", "title": "Carpenters and Joiners", "description": "Cutting, shaping, and fitting wood"},
    {"isco_code": "7121", "title": "Roofers", "description": "Constructing and repairing roofs"},
    {"isco_code": "7122", "title": "Floor Layers and Tile Setters", "description": "Laying floors and setting tiles"},
    {"isco_code": "7126", "title": "Plumbers and Pipe Fitters", "description": "Installing and repairing pipe systems"},
    {"isco_code": "7511", "title": "Butchers and Fishmongers", "description": "Slaughtering, cutting, processing meat and fish"},
    {"isco_code": "7512", "title": "Bakers, Pastry-cooks", "description": "Making bread, cakes, pastries"},
    {"isco_code": "7531", "title": "Tailors, Dressmakers, Furriers", "description": "Making, altering, repairing garments"},
    {"isco_code": "7532", "title": "Garment and Related Patternmakers", "description": "Making garment patterns"},
    {"isco_code": "7533", "title": "Sewing, Embroidery and Related Workers", "description": "Sewing, embroidering fabrics"},
    {"isco_code": "8322", "title": "Car, Taxi and Van Drivers", "description": "Driving motor cars, taxis, and vans"},
    {"isco_code": "8331", "title": "Bus and Tram Drivers", "description": "Driving buses and trams"},
    {"isco_code": "8332", "title": "Heavy Truck and Lorry Drivers", "description": "Driving heavy trucks"},
    {"isco_code": "9211", "title": "Crop Farm Labourers", "description": "Performing simple routine tasks on farms"},
    {"isco_code": "9212", "title": "Livestock Farm Labourers", "description": "Routine tasks in livestock production"},
    {"isco_code": "9312", "title": "Civil Engineering Labourers", "description": "Routine tasks in civil engineering"},
    {"isco_code": "9313", "title": "Building Construction Labourers", "description": "Carrying, lifting on construction sites"},
    {"isco_code": "9411", "title": "Fast Food Preparers", "description": "Preparing fast food meals"},
    {"isco_code": "9412", "title": "Kitchen Helpers", "description": "Cleaning kitchens, washing dishes"},
    {"isco_code": "5311", "title": "Child Care Workers", "description": "Attending to children's immediate needs"},
    {"isco_code": "5322", "title": "Home-Based Personal Care Workers", "description": "Providing personal care at home"},
    {"isco_code": "5141", "title": "Hairdressers", "description": "Cutting, styling, colouring hair"},
    {"isco_code": "5142", "title": "Beauticians", "description": "Providing beauty treatments"},
    {"isco_code": "2511", "title": "Systems Analysts", "description": "Analysing systems and designing solutions"},
    {"isco_code": "2512", "title": "Software Developers", "description": "Developing and maintaining software"},
    {"isco_code": "2513", "title": "Web and Multimedia Developers", "description": "Combining design with software"},
    {"isco_code": "2514", "title": "Applications Programmers", "description": "Writing and maintaining programs"},
    {"isco_code": "2431", "title": "Advertising and Marketing Professionals", "description": "Developing advertising campaigns"},
    {"isco_code": "2310", "title": "University and Higher Education Teachers", "description": "Teaching in higher education"},
    {"isco_code": "2320", "title": "Vocational Education Teachers", "description": "Teaching vocational subjects"},
    {"isco_code": "2330", "title": "Secondary Education Teachers", "description": "Teaching at secondary level"},
    {"isco_code": "2341", "title": "Primary School Teachers", "description": "Teaching at primary level"},
    {"isco_code": "3251", "title": "Dental Assistants and Therapists", "description": "Assisting dentists"},
    {"isco_code": "3256", "title": "Medical Assistants", "description": "Performing basic clinical tasks"},
    {"isco_code": "2240", "title": "Paramedical Practitioners", "description": "Providing advisory and preventive medical services"},
    {"isco_code": "1311", "title": "Agricultural and Forestry Production Managers", "description": "Managing farming operations"},
    {"isco_code": "1321", "title": "Manufacturing Managers", "description": "Managing manufacturing operations"},
    {"isco_code": "1420", "title": "Retail and Wholesale Trade Managers", "description": "Managing retail and wholesale operations"},
]


class TaxonomyLookupTool(BaseTool):
    """Searches ISCO-08 occupation table by text similarity."""

    name: str = "isco_lookup"
    description: str = (
        "Search ISCO-08 occupation taxonomy by text similarity. "
        "Input: a query string describing work experience. "
        "Returns: list of matching ISCO-08 occupations with codes, titles, and match scores."
    )
    context_id: str = Field(default="")

    async def _arun(self, query: str, context_id: str = "") -> list[dict]:
        """Async: search ISCO-08 reference table."""
        logger.debug("ISCO lookup: query='{}', context={}", query[:50], context_id or self.context_id)
        query_lower = query.lower()
        scored = []
        for entry in ISCO_08_REFERENCE:
            title_lower = entry["title"].lower()
            desc_lower = entry["description"].lower()
            score = 0.0
            query_words = query_lower.split()
            for word in query_words:
                if word in title_lower:
                    score += 0.4
                if word in desc_lower:
                    score += 0.2
            if score > 0:
                scored.append({
                    "isco_code": entry["isco_code"],
                    "title": entry["title"],
                    "description": entry["description"],
                    "match_score": min(score, 1.0),
                })
        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[:10]

    def _run(self, query: str, context_id: str = "") -> list[dict]:
        """Sync fallback."""
        import asyncio
        return asyncio.run(self._arun(query, context_id))
