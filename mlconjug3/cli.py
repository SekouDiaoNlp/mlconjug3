"""
cli.py

Command-line interface for mlconjug3.

This module exposes a Click-based CLI that allows users to conjugate verbs
in multiple languages using either rule-based or ML-based backends.

Features:
- Single or batch verb conjugation
- Optional output export (JSON/CSV)
- Config file support (TOML/YAML)
- Rich formatted terminal output
"""

import sys
import os
import csv
import json
import logging
import click
import tomlkit
import yaml

from rich.table import Table
from rich.console import Console
from mlconjug3.core.application_service import ConjugationApplicationService
from mlconjug3.core.options import EXPORT_FORMATS

try:
    from .utils import _
except Exception:
    def _(s: str) -> str:
        """
        Fallback no-op translation function used when gettext is not configured.
        """
        return s


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("verbs", nargs=-1)
@click.option(
    "-l",
    "--language",
    default="fr",
    help=_(
        "The language for the conjugation pipeline."
        " The values can be 'fr', 'en', 'es', 'it', 'pt' or 'ro'."
        " The default value is fr."
    ),
    type=click.STRING,
)
@click.option(
    "-o",
    "--output",
    default=None,
    help=_("Path of the filename for storing the conjugation tables."),
    type=click.STRING,
)
@click.option(
    "-s",
    "--subject",
    default="abbrev",
    help=_(
        "The subject format type for the conjugated forms."
        " The values can be 'abbrev' or 'pronoun'. The default value is 'abbrev'."
    ),
    type=click.STRING,
)
@click.option(
    "-f",
    "--file_format",
    default="json",
    help=_(
        "The output format for storing the conjugation tables."
        " The values can be 'json', 'csv'. The default value is 'json'."
    ),
    type=click.STRING,
)
@click.option(
    "-c",
    "--config",
    default=None,
    help=_(
        "Path of the configuration file for specifying language, subject, output file name and format."
        " Supported formats: toml, yaml"
    ),
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
)
def main(verbs, language, output, subject, file_format, config):
    """
    CLI entry point for mlconjug3.

    Examples
    --------
    Conjugate a verb:
        mlconjug3 -l en 'have'

    Conjugate multiple verbs:
        mlconjug3 -l fr 'aller' 'manger'

    Save output:
        mlconjug3 -l es -o output.json 'hablar'
    """
    config_options = load_config(config)

    language = config_options.get("language", language)
    subject = config_options.get("subject", subject)
    output = config_options.get("output", output)
    file_format = config_options.get("file_format", file_format)
    backend = config_options.get("backend", "legacy")
    theme_settings = config_options.get("theme", {})

    try:
        logger = logging.getLogger(__name__)
        console = Console()

        console_handler = logging.StreamHandler(sys.stdout)
        error_handler = logging.StreamHandler(sys.stderr)

        console_handler.setLevel(logging.INFO)
        error_handler.setLevel(logging.ERROR)

        logger.addHandler(console_handler)
        logger.addHandler(error_handler)
        logger.setLevel(logging.INFO)

        app_service = ConjugationApplicationService(
            language=language, subject=subject, backend=backend
        )
        normalized = app_service.conjugate_normalized(list(verbs))
        conjugations = normalized.conjugations
        missing = normalized.missing

        # -------------------------
        # Display results
        # -------------------------
        for verb, conjugation in conjugations.items():
            table = Table(
                title=f"Conjugation table for '{verb.capitalize()}'",
                show_header=True,
                header_style=theme_settings.get("header_style", "bold #0D47A1"),
            )

            table.add_column("Mood", style=theme_settings.get("mood_style", "bold #F9A825"))
            table.add_column("Tense", style=theme_settings.get("tense_style", "bold bright_magenta"))
            table.add_column("Person", style=theme_settings.get("person_style", "bold cyan"))
            table.add_column("Conjugation", style=theme_settings.get("conjugation_style", "bold #4CAF50"))

            for mood, tenses in conjugation.items():
                for tense, persons in tenses.items():
                    if isinstance(persons, dict):
                        for person, form in persons.items():
                            table.add_row(mood.capitalize(), tense.capitalize(), str(person), form)
                    else:
                        table.add_row(mood.capitalize(), tense.capitalize(), "", persons)

                    table.add_section()

                table.add_section()

            console.print(table)

        # -------------------------
        # Missing verbs
        # -------------------------
        if missing:
            for verb in missing:
                console.print(f"The verb '{verb}' could not be conjugated.")

        # -------------------------
        # Output export
        # -------------------------
        if output:
            if file_format == "json":
                with open(output, "w", encoding="utf-8") as outfile:
                    json.dump(conjugations, outfile)

            elif file_format == "csv":
                with open(output, "w", newline="", encoding="utf-8") as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(["Verb", "Mood", "Tense", "Person", "Conjugation"])

                    for verb, conjugation in conjugations.items():
                        for mood, tenses in conjugation.items():
                            for tense, persons in tenses.items():
                                if isinstance(persons, dict):
                                    for person, form in persons.items():
                                        writer.writerow([verb, mood, tense, person, form])
                                else:
                                    writer.writerow([verb, mood, tense, "", persons])

            else:
                raise ValueError(
                    f"Invalid output format. Please choose one of {sorted(EXPORT_FORMATS)}."
                )

    except Exception as e:
        logging.error("An error occurred: {}".format(e))

        if output:
            click.echo(
                "Conjugations not saved. Please check the output file path and permissions."
            )
        else:
            click.echo(
                "Conjugations not displayed. Please check the input verbs and language."
            )

        sys.exit(1)


def load_config(config):
    """
    Load configuration file (TOML or YAML).

    Parameters
    ----------
    config : str or None
        Path to configuration file.

    Returns
    -------
    dict
        Parsed configuration dictionary.
    """
    if not config:
        home = os.path.expanduser("~")
        config = os.path.join(home, "mlconjug3/config.toml")

        if not os.path.isfile(config):
            config = os.path.join(home, "mlconjug3/config.yaml")

            if not os.path.isfile(config):
                return {}

    config_options = {}

    if config.endswith(".toml"):
        with open(config, "r", encoding="utf-8") as config_file:
            config_options = tomlkit.loads(config_file.read())

    elif config.endswith(".yaml") or config.endswith(".yml"):
        with open(config, "r", encoding="utf-8") as config_file:
            config_options = yaml.load(config_file, Loader=yaml.FullLoader)

    return config_options


if __name__ == "__main__":
    main()
