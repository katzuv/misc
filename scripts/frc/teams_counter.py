import click

CONTEXT = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT)
@click.option(
    "-k",
    "--key",
    "api_key",
    required=True,
    prompt=True,
    hide_input=True,
    envvar="TBA_AUTH_KEY",
    show_envvar=True,
    help="TBA API authorization key",
)
def cli():
    pass


if __name__ == "__main__":
    cli()
