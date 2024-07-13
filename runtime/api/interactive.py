from cli import *
from click.exceptions import UsageError
import readline  

# Load history file if it exists
HISTFILE = '.cli_history'
try:
    readline.read_history_file(HISTFILE)
except FileNotFoundError:
    pass

if __name__ == '__main__':
    click.echo("Interactive mode. Enter command (type 'exit' to quit or '--help'):")
    while True:
        try:
            command = input("> ")
            if command.lower() in ["exit", ":q"]:
                break
            cli.main(args=command.split(), standalone_mode=False)            
        except SystemExit:
            pass  # Prevent Click from calling sys.exit()
        except UsageError as e:
            click.echo(f"Error: {e}")
            pass  # Prevent Click from calling sys.exit()
        except click.MissingParameter as e:
            click.echo(f"Missing parameter: {e}")
        except click.BadOptionUsage as e:
            click.echo(f"Bad option: {e}")
        except KeyboardInterrupt:
            click.echo("\nExiting...")
            break        
        
readline.write_history_file(HISTFILE)