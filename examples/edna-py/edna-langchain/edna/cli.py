"""CLI interface for EDNA."""

import argparse
import logging
import sys
from pathlib import Path
from .config import setup_logging, Config, DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from .suggest import generate_suggestions

logger = logging.getLogger(__name__)


def suggest_command(args):
    """Execute the suggest command."""
    
    # Setup configuration
    config = Config()
    if not config.validate():
        sys.exit(1)
    
    # Setup paths
    data_dir = Path(DEFAULT_DATA_DIR)
    output_path = Path(args.emit)
    
    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate suggestions
    try:
        suggestions = generate_suggestions(
            data_dir=data_dir,
            output_path=output_path,
            since_days=args.since_days,
            limit=args.limit,
            channel_override=args.channel,
            mark_as_sent=args.mark_as_sent,
            dry_run=not args.mark_as_sent
        )
        
        if suggestions:
            logger.info(f"Successfully generated {len(suggestions)} suggestions")
        else:
            logger.warning("No suggestions generated")
            
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="EDNA - Engagement Development Nudge Agent"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Suggest command
    suggest_parser = subparsers.add_parser(
        "suggest",
        help="Generate nudge suggestions for mentor-mentee pairs"
    )
    
    suggest_parser.add_argument(
        "--since-days",
        type=int,
        default=30,
        help="Filter pairs with activity in last N days (default: 30)"
    )
    
    suggest_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of suggestions to generate (default: 20)"
    )
    
    suggest_parser.add_argument(
        "--channel",
        choices=["email", "in_app", "slack"],
        help="Override communication channel"
    )
    
    suggest_parser.add_argument(
        "--emit",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR / "edna_suggestions.jsonl"),
        help="Output path for suggestions JSONL"
    )
    
    suggest_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run without updating sent log (default: true)"
    )
    
    suggest_parser.add_argument(
        "--mark-as-sent",
        action="store_true",
        help="Mark suggestions as sent in log file"
    )
    
    suggest_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(verbose=getattr(args, 'verbose', False))
    
    # Execute command
    if args.command == "suggest":
        suggest_command(args)


if __name__ == "__main__":
    main()