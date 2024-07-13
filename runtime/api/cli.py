import click


@click.command()
def trade_today():
    """Advise on trades that should be made today"""
    click.echo("TODO: Advise on trades that should be made today")


# Create a Click group to hold the commands
@click.group()
def cli():
    pass


# Add the commands to the group
cli.add_command(trade_today)

if __name__ == "__main__":
    cli()
