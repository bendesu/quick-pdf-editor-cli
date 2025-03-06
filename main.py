from typing import Literal, Optional

import click

from libs.core_quick_pdf import CoreQuickPdf

VERSION = "0.0.1"

Option = Literal["--file", "--output", "--content"]


def verify_options(options: list[tuple[Option, Optional[str]]]):
    missing_options: list[Option] = []
    for opt in options:
        if opt[1] is None:
            missing_options.append(opt[0])

    if len(missing_options) > 0:
        raise click.BadParameter(", ".join([f"'{opt}'" for opt in missing_options]))


@click.command()
@click.argument("action", type=click.Choice(["EXPORT-CONTENT", "UPDATE-CONTENT"], case_sensitive=False))
@click.option("--file", "-f", type=click.Path(exists=True), help="Input file path")
@click.option("--output", "-o", type=click.Path(exists=False), help="Output file path")
@click.option("--content", "-c", type=click.Path(exists=True), help="Content JSON file path")
def cli_app(action, file, output, content):
    core = CoreQuickPdf(VERSION)
    match action:
        case "EXPORT-CONTENT":
            verify_options([("--file", file), ("--output", output)])
            core.load_pdf(file)
            core.export_pdf_content(output)
        case "UPDATE-CONTENT":
            verify_options([("--file", file), ("--content", content), ("--output", output)])
            core.load_pdf(file)
            core.load_pdf_content(content)
            core.export_pdf(output)


if __name__ == '__main__':
    cli_app()
