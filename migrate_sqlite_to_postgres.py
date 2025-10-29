#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for UmbreonBot2

This script migrates data from the existing SQLite database to PostgreSQL.
Run this ONCE after setting up PostgreSQL and before starting the bot with the new database.

Usage:
    python migrate_sqlite_to_postgres.py

Requirements:
    - SQLite database file (bot.db) exists
    - PostgreSQL server is running
    - Environment variables are set in vars.env
    - psycopg2-binary is installed
"""

import os
import sqlite3
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv("./vars.env")

SQLITE_DB = "bot.db"

def get_postgres_connection():
    """Create and return a PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "umbreon"),
        user=os.getenv("POSTGRES_USER", "umbreon"),
        password=os.getenv("POSTGRES_PASSWORD", "umbreon_pwd"),
    )

def copy_table(sqlite_cur, pg_cur, table_name, columns, insert_sql, transform_fn=None):
    """Copy data from SQLite table to PostgreSQL table."""
    try:
        # Check if table exists in SQLite
        sqlite_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not sqlite_cur.fetchone():
            print(f"⚠️  Table '{table_name}' not found in SQLite database, skipping...")
            return 0

        # Get all rows from SQLite
        sqlite_cur.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
        rows = sqlite_cur.fetchall()

        if not rows:
            print(f"📝 Table '{table_name}' is empty, skipping...")
            return 0

        migrated = 0
        skipped = 0

        for row in rows:
            try:
                # Apply transformation function if provided
                if transform_fn:
                    row = transform_fn(row)

                pg_cur.execute(insert_sql, row)
                migrated += 1
            except psycopg2.IntegrityError as e:
                # Skip duplicates or constraint violations
                skipped += 1
                print(f"⚠️  Skipped row in {table_name}: {e}")
            except Exception as e:
                skipped += 1
                print(f"❌ Error migrating row in {table_name}: {row} -> {e}")

        print(f"✅ {table_name}: {migrated} rows migrated, {skipped} skipped")
        return migrated

    except Exception as e:
        print(f"❌ Failed to migrate table {table_name}: {e}")
        return 0

def transform_levels(row):
    """Transform levels table data if needed."""
    level, xp, user_id, guild_id = row
    # Ensure values are not None and convert to proper types
    return (
        guild_id or 0,
        user_id or 0,
        level or 0,
        xp or 0
    )

def transform_boolean(row, bool_index):
    """Transform boolean values from SQLite INTEGER to PostgreSQL BOOLEAN."""
    row_list = list(row)
    # Convert SQLite boolean (0/1) to PostgreSQL boolean
    if row_list[bool_index] is not None:
        row_list[bool_index] = bool(row_list[bool_index])
    else:
        row_list[bool_index] = False
    return tuple(row_list)

def main():
    """Main migration function."""
    print("🚀 Starting SQLite to PostgreSQL migration...")

    # Check if SQLite database exists
    if not os.path.exists(SQLITE_DB):
        print(f"❌ SQLite database '{SQLITE_DB}' not found!")
        print("If you don't have existing data, you can skip this migration.")
        return

    try:
        # Connect to both databases
        pg_conn = get_postgres_connection()
        sqlite_conn = sqlite3.connect(SQLITE_DB)

        print("✅ Connected to both databases")

        with sqlite_conn, pg_conn:
            sqlite_cur = sqlite_conn.cursor()
            pg_cur = pg_conn.cursor()

            total_migrated = 0

            # Migrate levels table (reordered columns for new schema)
            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "levels",
                ["level", "xp", "user", "guild"],
                'INSERT INTO levels (guild, user_id, level, xp) VALUES (%s, %s, %s, %s) ON CONFLICT (guild, user_id) DO UPDATE SET level=EXCLUDED.level, xp=EXCLUDED.xp',
                transform_levels
            )

            # Migrate twitch table
            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "twitch",
                ["twitch_user", "status", "guild_id"],
                "INSERT INTO twitch (twitch_user, status, guild_id) VALUES (%s, %s, %s) ON CONFLICT (twitch_user, guild_id) DO UPDATE SET status=EXCLUDED.status"
            )

            # Migrate levelsettings table (with boolean conversion)
            def transform_levelsettings(row):
                return transform_boolean(row, 0)  # levelsys is at index 0

            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "levelsettings",
                ["levelsys", "role", "levelreq", "message", "guild_id"],
                "INSERT INTO levelsettings (levelsys, role, levelreq, message, guild_id) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (guild_id) DO UPDATE SET levelsys=EXCLUDED.levelsys, role=EXCLUDED.role, levelreq=EXCLUDED.levelreq, message=EXCLUDED.message",
                transform_levelsettings
            )

            # Migrate welcome table
            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "welcome",
                ["guild_id", "welcome_channel_id", "welcome_message", "welcome_dm", "welcome_gif_url"],
                "INSERT INTO welcome (guild_id, welcome_channel_id, welcome_message, welcome_dm, welcome_gif_url) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (guild_id) DO UPDATE SET welcome_channel_id=EXCLUDED.welcome_channel_id, welcome_message=EXCLUDED.welcome_message, welcome_dm=EXCLUDED.welcome_dm, welcome_gif_url=EXCLUDED.welcome_gif_url"
            )

            # Migrate levelup table
            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "levelup",
                ["guild_id", "levelup_channel_id"],
                "INSERT INTO levelup (guild_id, levelup_channel_id) VALUES (%s, %s) ON CONFLICT (guild_id) DO UPDATE SET levelup_channel_id=EXCLUDED.levelup_channel_id"
            )

            # Migrate twitch_config table
            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "twitch_config",
                ["guild_id", "twitch_channel_id"],
                "INSERT INTO twitch_config (guild_id, twitch_channel_id) VALUES (%s, %s) ON CONFLICT (guild_id) DO UPDATE SET twitch_channel_id=EXCLUDED.twitch_channel_id"
            )

            # Migrate rps table
            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "rps",
                ["guild_id", "user_id", "score"],
                "INSERT INTO rps (guild_id, user_id, score) VALUES (%s, %s, %s) ON CONFLICT (guild_id, user_id) DO UPDATE SET score=EXCLUDED.score"
            )

            # Migrate defaultrole table
            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "defaultrole",
                ["guild_id", "role_id"],
                "INSERT INTO defaultrole (guild_id, role_id) VALUES (%s, %s) ON CONFLICT (guild_id) DO UPDATE SET role_id=EXCLUDED.role_id"
            )

            # Migrate logsettings table (with boolean conversion)
            def transform_logsettings(row):
                if len(row) == 2:
                    # If is_enabled column is missing, add default False
                    return row + (False,)
                return transform_boolean(row, 2)  # is_enabled is at index 2

            total_migrated += copy_table(
                sqlite_cur, pg_cur,
                "logsettings",
                ["guild_id", "log_channel_id", "is_enabled"],
                "INSERT INTO logsettings (guild_id, log_channel_id, is_enabled) VALUES (%s, %s, %s) ON CONFLICT (guild_id) DO UPDATE SET log_channel_id=EXCLUDED.log_channel_id, is_enabled=EXCLUDED.is_enabled",
                transform_logsettings
            )

            pg_conn.commit()
            print(f"\n🎉 Migration completed successfully!")
            print(f"📊 Total rows migrated: {total_migrated}")

    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        print("Make sure PostgreSQL is running and credentials are correct.")
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("UmbreonBot2 - SQLite to PostgreSQL Migration")
    print("=" * 60)

    response = input("Do you want to proceed with the migration? (y/N): ").lower().strip()
    if response in ['y', 'yes']:
        main()
    else:
        print("Migration cancelled.")
