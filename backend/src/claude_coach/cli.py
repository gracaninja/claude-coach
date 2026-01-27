"""Command-line interface for Claude-Coach."""

import argparse
import sys
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude-Coach: Extract insights from Claude Code logs"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import Claude Code logs")
    import_parser.add_argument(
        "--claude-dir",
        type=Path,
        default=None,
        help="Path to Claude config directory (default: ~/.claude)",
    )
    import_parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to database file (default: ~/.claude-coach/claude_coach.db)",
    )
    import_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-import of existing sessions",
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show quick statistics")
    stats_parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to database file",
    )

    args = parser.parse_args()

    if args.command == "import":
        cmd_import(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()
        sys.exit(1)


def cmd_import(args):
    """Handle import command."""
    from claude_coach.core.importer import LogImporter

    print(f"Importing Claude Code logs...")
    if args.claude_dir:
        print(f"  Claude directory: {args.claude_dir}")
    if args.db:
        print(f"  Database: {args.db}")
    if args.force:
        print("  Force re-import: enabled")

    importer = LogImporter(claude_dir=args.claude_dir, db_path=args.db)
    stats = importer.import_all(force=args.force)

    print(f"\nImport complete:")
    print(f"  Sessions imported: {stats['sessions_imported']}")
    print(f"  Sessions skipped: {stats['sessions_skipped']}")
    print(f"  Messages imported: {stats['messages_imported']}")
    print(f"  Tool usages imported: {stats['tool_usages_imported']}")
    print(f"  Errors imported: {stats['errors_imported']}")


def cmd_serve(args):
    """Handle serve command."""
    import uvicorn

    print(f"Starting Claude-Coach API server...")
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  API docs: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "claude_coach.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def cmd_stats(args):
    """Handle stats command."""
    from claude_coach.models import get_session_factory, Session, ToolUsage, ErrorEvent

    session_factory = get_session_factory(args.db)

    with session_factory() as db:
        session_count = db.query(Session).count()
        total_messages = sum(s.message_count for s in db.query(Session).all())
        total_tokens = sum(
            s.total_input_tokens + s.total_output_tokens
            for s in db.query(Session).all()
        )
        tool_count = db.query(ToolUsage).count()
        error_count = db.query(ErrorEvent).count()

        # Top tools
        from sqlalchemy import func
        top_tools = (
            db.query(ToolUsage.tool_name, func.count(ToolUsage.id).label("count"))
            .group_by(ToolUsage.tool_name)
            .order_by(func.count(ToolUsage.id).desc())
            .limit(5)
            .all()
        )

    print("\n=== Claude-Coach Statistics ===\n")
    print(f"Sessions:     {session_count}")
    print(f"Messages:     {total_messages}")
    print(f"Total Tokens: {total_tokens:,}")
    print(f"Tool Calls:   {tool_count}")
    print(f"Errors:       {error_count}")

    if top_tools:
        print("\nTop 5 Tools:")
        for tool_name, count in top_tools:
            print(f"  {tool_name}: {count}")


if __name__ == "__main__":
    main()
