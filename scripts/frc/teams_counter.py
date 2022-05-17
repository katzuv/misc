import click

CONTEXT = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT)
def cli():
    pass


if __name__ == "__main__":
    cli()
