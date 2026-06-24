"""CLI entrypoint for the sleepybricks application."""

import typer

from sleepybricks.cli.commands import registerCommands
from sleepybricks.core.logging import configureLogging

app = typer.Typer(
    add_completion=False,
    help="Run databricks operations across multiple workspaces from one terse CLI.",
)

configureLogging()
registerCommands(app)


def main() -> None:
    """Run the sleepybricks CLI application."""

    app()


if __name__ == "__main__":
    main()
