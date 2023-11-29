import click
import uvicorn

from bionet.w3 import deploy_contract, register_user, is_authorized_user, remove_user


@click.group()
def cli():
    pass


@cli.command()
@click.option("--port", default=5000, help="server port number")
def guard(port):
    """Start bionet guard server"""
    uvicorn.run("bionet.server:app", port=port, log_level="info")


@cli.command()
def wallet():
    """Generate a wallet. Printing relevent information to the screen"""
    from eth_account import Account

    account = Account.create()
    click.echo(f" address  : {account.address}")
    click.echo(f" secretkey: {account.key.hex()}")


@cli.command()
def deploy():
    """Deploy the service registry contract"""
    contract_address = deploy_contract()
    click.echo(" Service Registry Deployed!")
    click.echo(f" contract address  : {contract_address}")


@cli.command()
@click.option(
    "--user", prompt="User address", help="The wallet address of the user to register"
)
def register(user):
    """Register a user with the service"""
    result = register_user(user)
    click.echo(" User registered!")
    click.echo(f" tx receipt  : {result}")


@cli.command()
@click.option(
    "--user", prompt="User address", help="The wallet address of the user to check"
)
def is_valid(user):
    """Check if the user is valid"""
    is_valid = is_authorized_user(user)
    if is_valid:
        click.echo(" User IS authorized")
    else:
        click.echo(" User IS NOT authorized")


@cli.command()
@click.option(
    "--user", prompt="User address", help="The wallet address of the user to remove"
)
def remove(user):
    """Remove the user from the service"""
    result = remove_user(user)
    click.echo(" User removed!")
    click.echo(f" tx receipt  : {result}")


## Commands below are used for the example ##


@cli.command()
def service():
    """Start example DNA service. Remember to start the guard first"""
    click.echo("Starting example DNA service...")
    uvicorn.run("example.dnaservice:app", port=8080, log_level="info")


@cli.command()
def good_user():
    from example.user import can_access_service

    is_valid = can_access_service()
    if is_valid:
        click.echo(" SUCCESS!  Alice is a verified, registered user of the service")
    else:
        click.echo(" FAIL!  Alice is not authorized to use the service")
