"""CLI entrypoint for NAKSHA."""
import argparse
import sys
from naksha.core.config import get_settings
from naksha.cli.seed import seed_postgres


def main() -> None:
    parser = argparse.ArgumentParser(description="NAKSHA Land Intelligence Engine CLI")
    subparsers = parser.add_subparsers(dest="subcommand", help="Sub-commands")

    # seed command
    seed_parser = subparsers.add_parser("seed", help="Seed database with benchmark records and cadastral layers")
    seed_parser.add_argument(
        "--target",
        choices=["postgres", "sqlite"],
        default="postgres",
        help="Target database engine (default: postgres)",
    )
    seed_parser.add_argument(
        "--url",
        default=None,
        help="Explicit database URL override (defaults to settings.database_url or NAKSHA_TEST_DATABASE_URL)",
    )
    seed_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Bypass database name safety confirmation for non-dev/non-test databases",
    )

    args = parser.parse_args()

    if args.subcommand == "seed":
        settings = get_settings()
        if args.target == "postgres":
            target_url = args.url or settings.database_url
            if not target_url.startswith("postgresql"):
                # If settings.database_url is sqlite (default), fall back to test_database_url if available
                target_url = settings.test_database_url or "postgresql+psycopg://naksha_dev:naksha_dev_pw@localhost:5432/naksha_dev"

            print(f"[NAKSHA CLI] Seeding PostgreSQL at {target_url} (safety check: --yes={args.yes})...")
            try:
                counts = seed_postgres(target_url, yes=args.yes)
                print("[NAKSHA CLI] Seeding completed successfully:")
                for k, v in counts.items():
                    print(f"  - {k}: {v}")
            except Exception as e:
                print(f"[NAKSHA CLI ERROR] Seeding aborted: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("[NAKSHA CLI] SQLite synthetic seeding is initialized automatically in-memory/on-start.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
