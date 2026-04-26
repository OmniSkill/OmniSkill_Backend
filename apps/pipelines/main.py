"""Prefect data pipeline flows for UNMAPPED."""

from __future__ import annotations

import httpx
from loguru import logger
from prefect import flow, task


@task(retries=3, retry_delay_seconds=10)
async def fetch_ilostat_data(endpoint: str, country_code: str) -> dict:
    """Fetch labour statistics from ILOSTAT API."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://www.ilo.org/ilostat/api/v1/{endpoint}",
            params={"country": country_code, "format": "json"},
        )
        resp.raise_for_status()
        return resp.json()


@task(retries=3, retry_delay_seconds=10)
async def fetch_world_bank_data(indicator: str, country_code: str) -> dict:
    """Fetch development indicators from World Bank API."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}",
            params={"format": "json", "per_page": 100},
        )
        resp.raise_for_status()
        return resp.json()


@task
async def transform_labour_data(raw_data: dict, context_id: str) -> dict:
    """Transform raw API data into normalised format."""
    logger.info("Transforming labour data for context {}", context_id)
    return {"context_id": context_id, "records": [], "source": "ilostat"}


@flow(name="unmapped-data-pipeline")
async def data_pipeline_flow(context_id: str = "gha-urban-2024") -> dict:
    """Main data ingestion pipeline for a country context."""
    logger.info("Starting data pipeline for {}", context_id)

    country_code = context_id.split("-")[0].upper()

    ilostat_data = await fetch_ilostat_data("employment", country_code)
    wdi_data = await fetch_world_bank_data("SL.TLF.TOTL.IN", country_code)
    transformed = await transform_labour_data(ilostat_data, context_id)

    logger.info(
        "Pipeline complete for {} – {} ILO records, {} WDI records",
        context_id,
        len(ilostat_data.get("data", [])),
        len(wdi_data) if isinstance(wdi_data, list) else 0,
    )

    return {"context_id": context_id, "status": "complete", "data": transformed}


if __name__ == "__main__":
    import asyncio

    asyncio.run(data_pipeline_flow())
