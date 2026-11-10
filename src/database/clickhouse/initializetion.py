from src.database.clickhouse.client import get_ch_client

import logging
logger = logging.getLogger(__name__)


def initializetion_row_tables():
    client = get_ch_client()

    try:

        client.command("""
        CREATE DATABASE IF NOT EXISTS row
        """)

        client.command("""
        CREATE TABLE IF NOT EXISTS row.regions(
        region_id Int32,
        region_name String
        )
        ENGINE = MergeTree
        ORDER BY region_id
        """)

        client.command("""
        CREATE TABLE IF NOT EXISTS row.leagues(
        league_id Int32,
        competition_type String,
        stage_type Int8,
        category_id Int8,
        league_name String,
        region_id Int32
        )
        ENGINE = MergeTree
        ORDER BY league_id
        """)

        client.command("""
        CREATE TABLE IF NOT EXISTS row.seasons (
        season_id Int32,
        start_date Int32,
        end_date Int32,
        is_current Bool,
        league_id Int32,
        updated_at DateTime64(3)
        )
        ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY season_id
        """)

        client.command("""
        CREATE TABLE IF NOT EXISTS row.teams 
        (
        team_id Int32,
        team_name String
        )
        ENGINE = MergeTree
        ORDER BY team_id
        """)

        client.command("""
        CREATE TABLE IF NOT EXISTS row.season_team_relations
        (
        season_id Int32,
        team_id Int32,
        count_matches Int8,
        updated_at DateTime64(3)
        )
        ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (season_id, team_id)
        """)

        client.command("""
        CREATE TABLE IF NOT EXISTS row.matches (
        match_id Int32,
        time DateTime64(3),
        home_team_id Int32,
        away_team_id Int32,
        home_score Nullable(Int16),
        away_score Nullable(Int16),
        home_penalties Nullable(Int16),
        away_penalties Nullable(Int16),
        status String,
        season_id Int32,
        league_id Int32,
        )
        ENGINE = MergeTree
        PARTITION BY toYYYYMM(time)
        ORDER BY (league_id, season_id, match_id)
        """)

    except Exception:
        logger.exception("Failed to initialize ClickHouse tables")
        raise