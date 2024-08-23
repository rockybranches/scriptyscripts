import shlex
import itertools
import click
import os
import sys
from pathlib import Path
from difflib import get_close_matches
import subprocess
from typing import List
import importlib
from trogon import tui

#: import interactive_pager
interactive_pager = importlib.import_module(
    ".tools.interactive_pager",
    package="scriptyscripts"
).interactive_pager


#: path to ~/scriptyscripts
pth = Path(os.getenv("HOME")).joinpath("scriptyscripts")


def get_version_from_poetry():
    output = subprocess.run(
        ['poetry', 'version', '--short'],
        check=True, text=True, capture_output=True,
        cwd=str(pth.joinpath("sscripts"))
    )
    if output is None:
        raise RuntimeError("Failed to get version from poetry.")
    return output.stdout.strip()


@tui(command="ui", help="open terminal UI")
@click.version_option()
@click.group()
@click.pass_context
def cli(ctx):
    if not ctx.obj:
        ctx.obj = ctx.ensure_object(dict)
    return ctx


@cli.command("version")
def print_version():
    """Print the version of scriptyscripts."""
    click.secho(get_version_from_poetry(), color='success', bold=True)


@cli.command("path")
def print_path():
    """print the scriptyscriptys path (should be ~/scriptyscripts)."""
    click.secho(str(pth.absolute().resolve()))


def get_matches(ctx, param, value, n=1, cutoff=0.1) -> List[str]:
    command = value
    results = search_scriptyscripts(ctx, None, '*')
    if n <= 0:
        n = len(results)
    matches = get_close_matches(command, results, n=n, cutoff=cutoff)
    if isinstance(matches, str):
        matches = [matches, ]
    n_matches = len(matches)
    ctx.obj['n_matches'] = n_matches
    match n_matches:
        case 0:
            # error for zero results
            click.secho(f"No scriptyscripts command matching '{command}' was found.", err=True)
            exit(1)
        case 1:
            #: handle a single result (always return a List[str])
            return [matches[0], ]
        case _:
            # handle more than 1 result
            return matches


def generate_pager_results(results, interactive=True):
    """utilizes an (non-)interactive pager"""
    match interactive:
        case True:
            # flush stdout and stderr before running pager
            sys.stdout.flush()
            sys.stderr.flush()
            selection = interactive_pager(results)
            sys.stdout.flush()
            sys.stderr.flush()
            click.secho(
                selection, color='success', blink=False, bold=True
            )
            sys.stdout.flush()
            sys.stderr.flush()
            return selection
        case False:
            # flush stdout and stderr before printing results
            sys.stdout.flush()
            sys.stderr.flush()
            output = "\n".join([result.strip() for result in results])
            click.secho(output, color='green')
            sys.stdout.flush()
            sys.stderr.flush()
            separator = "=" * 10
            click.secho(
                f"""\n\n{
                    separator}\n\nClosest match:\n\n\t{results[-1]}\n\n""",
                color='success', bold=True, blink=False
            )
            sys.stdout.flush()
            sys.stderr.flush()
            return output


def search_scriptyscripts(ctx, param, value, n=-1, cutoff=0.1):
    """Search for scriptyscripts commands."""

    @click.pass_context
    def update_context(ctx, param, value):
        if not ctx.obj:
            ctx.obj = ctx.ensure_object(dict)
        if hasattr(param, 'name'):
            ctx.obj[f'_orig.{param.name}'] = value
        return ctx

    n = ctx.params.get('n', n)

    if len(value) == 0:
        value = "*"
    else:
        value = "".join(value)

    ctx = update_context(param, value)

    results = pth.glob(value)

    #: exclude emacs backup files
    results = [str(r) for r in itertools.filterfalse(
        lambda r: str(r)[-1] == '~', results)]

    #: handle no results
    if len(results) == 0:
        results = get_matches(ctx, param, value, n=n, cutoff=cutoff)
    return results


@cli.command("list")
@click.argument("glob_pattern", nargs=-1, callback=search_scriptyscripts)
@click.option("-n", "--n", "--N", default=10, help="Maximum number of results to show")
@click.option("--pager/--no-pager", is_flag=True, default=False,
              help="Whether or not to use a pager to display results")
@click.pass_context
def list_commands(ctx, glob_pattern, n, pager):
    """List the commands in ~/scriptyscripts matching GLOB_PATTERN.

    GLOB_PATTERN is a regex-like search pattern, e.g. 'test-*'.
    """
    click.secho(
        "\nMatching scriptyscripts commands:",
        color='success', bold=True, blink=False)
    results = [g.strip() for g in reversed(glob_pattern)]  # ! after callback
    nresults = ctx.obj.get('n_matches', len(results))
    if nresults > n:
        results = results[:n]
    match nresults:
        case 0:
            click.secho("failed to find any matching commands!", err=1)
            exit(1)
        case 1:
            click.secho(results[0], color='success', bold=True)
        case _:
            generate_pager_results(results, interactive=pager)
    return True


def search_scriptyscripts_run(ctx, param, value, n=5, cutoff=0.1):
    return search_scriptyscripts(ctx, param, value, n=n, cutoff=cutoff)


def handle_results(ctx, results, interactive=True):
    """handle results depending on number of results (n_matches)"""
    nresults = ctx.obj.get('n_matches', len(results))
    match nresults:
        case 0:
            raise RuntimeError("No matching scriptyscripts command was found.")
        case 1:
            command = results[0]
        case _:
            # handle results interactively
            command = generate_pager_results(results, interactive=interactive)
    return command


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.argument("command", nargs=1, required=True, type=click.UNPROCESSED,
                callback=search_scriptyscripts_run)
@click.argument("args", nargs=-1, required=False, type=click.UNPROCESSED)
@click.pass_context
def run(ctx, command, args):
    """"
    Execute the given COMMAND (should match something in the ~/scriptyscripts directory).

    COMMAND given command in the ~/scriptyscripts directory.
    ARGS arguments for the given command (if needed).
    """
    # handle results after running search...
    results = [c for c in command] if not isinstance(command, str) \
        else [command, ]
    command = handle_results(ctx, results, interactive=True)

    # handle missing args
    if args is None:
        args = []

    # execute command
    subprocess.run(shlex.split(command) + [a for a in args], check=True)


@cli.command()
@click.argument("command", nargs=1, required=False, type=click.types.StringParamType(),
                callback=search_scriptyscripts_run)
@click.option("--editor",
              default='subl',
              help="Choose the editor to use.",
              type=click.types.Choice(
              ("subl", os.getenv('EDITOR', 'emacs'), 'emacs', "code", "code-insiders", "curside", "cursor.AppImage"))
)
@click.pass_context
def edit(ctx, command, editor):
    """Edit the specified command in emacs.

    Edit `command`: Edit a command script from the ~/scriptyscripts directory.
    ...otherwise opens `editor` in the ~/scriptyscripts/scriptyscripts package directory.
    """

    # ensure scriptyscripts package dir is given as default
    if command is None:
        project_folder = os.path.expanduser('~/scriptyscripts/scriptyscripts/scriptyscripts.sublime-project')
        match editor:
            case "subl":
                command = ['--new-window', '--project', project_folder]
            case "emacs":
                command = [project_folder.split("/")[0]]
            case _:
                command = ['--new-window', project_folder.split("/")[0]]

    # ! ensure search results are handled as a list (once returned from callback)
    if not isinstance(command, list):
        command = [command]
    command: List = [c for c in command]

    # handle search results interactively
    command = handle_results(ctx, command, interactive=True)
    if not isinstance(command, list):
        command = [command]
    command: List = [c for c in command]

    import time
    click.secho(f"Editing: '{command}' (using {editor})...", color='success', bold=True)
    time.sleep(1)
    # countdown indicator
    for i in range(2, 0, -1):
        click.secho(f"Editing selected command '{command}' with editor '{editor}' in {i} seconds...", color='success', bold=True)
        time.sleep(1)
    # execute editor process
    if not isinstance(command, list):
        command = [command] # ! ensure it's a list!
    subprocess.run([editor] + command, check=True)


@cli.command()
@click.option(
    "--bump/--no-bump", is_flag=True, default=True, help="Bump version"
)
@click.option(
    "--version",
    help="Set version",
    type=click.types.Choice(
        ['major', 'minor', 'patch', 'prepatch', 'preminor', 'premajor']),
    default='patch'
)
@click.option(
    "--backup/--no-backup",
    is_flag=True,
    default=True,
    help="Backup to remote git repo"
)
@click.option("--install-path", type=click.Path(exists=True),
              default=None,
              help="Path to install scriptyscripts to")
@click.option("--local-pypi-path", type=click.Path(exists=True),
              default=os.path.expanduser("~/media/pypi-packages"),
              help="Path to local pypi repo")
def upgrade(bump, version, backup, install_path, local_pypi_path):
    """Update scriptyscripts to the local HEAD."""
    click.secho("Upgrading scriptyscripts...", color='success', bold=True)
    # get the working directory for the scriptyscripts installation
    default_shell_cwd = Path(__file__).parent.joinpath('..').absolute()
    if install_path is None:
        install_path = default_shell_cwd
    if not Path(install_path).exists():
        click.secho(
            f"""Install path {install_path} does not exist. Using default {
                default_shell_cwd}""",
            color='warning', bold=True)
        install_path = default_shell_cwd
    # set the working directory
    shell_cwd = Path(install_path)
    # check that the cwd is the scriptyscripts directory
    if not shell_cwd.joinpath("scriptyscripts").exists():
        raise RuntimeError(
            "scriptyscripts must be installed in the 'scriptyscripts' directory.")
    # bump the version
    if bump:
        subprocess.run(
            ['poetry', 'version', f'{version}'], check=True, cwd=shell_cwd)
    # install the new version
    subprocess.run(["poetry", "install"], check=True, cwd=shell_cwd)
    # upgrade in pipx
    subprocess.run(["pipx", "upgrade", "scriptyscripts"], check=True)
    # backup to remote git repo
    if backup:
        subprocess.run(['sh', '-c', 'backup-rcapps-config'], check=True)
    if local_pypi_path is not None and Path(local_pypi_path).exists():
        # copy the latest dist to the local pypi repo
        click.secho(
            f"Copying latest dist to local pypi repo at {local_pypi_path}...",
            color='success', bold=True)
        subprocess.run(["poetry", "build"], check=True, cwd=shell_cwd)
        subprocess.run(
            f'''SRC_DIR="$(ls -t dist/*.tar.gz | head -1)"; cp "$SRC_DIR" {
                str(local_pypi_path)}/''',
            check=True, shell=True)
        click.secho("Copying complete!", color='success', bold=True)
    click.secho("Upgrade complete!", color='success', bold=True)


@cli.command("link")
def link_scripts():
    """Link config & scripts locally."""
    click.secho("Linking config & scripts...", color='success', bold=True)
    subprocess.run(['sh', '-c', 'link_scripts'], check=True)
    click.secho("Linking complete!", color='success', bold=True)


@cli.command("completions")
@click.option("--shell", type=click.types.Choice(['zsh', 'bash']),
              default='zsh', help="Shell to generate completions for")
def completions(shell):
    """Generate shell completions for scriptyscripts."""
    click.secho("Generating shell completions for scriptyscripts...",
                color='success', bold=True)
    completions_funcs_path = os.path.join(
        os.path.dirname(__file__),
        'scripts', 'generate-scriptyscripts-completions.sh'
    )
    user_response = click.prompt(
        "This will modify your shell's startup file (e.g. .zshrc or .bashrc).\n"
        "Would you like to continue?",
        type=click.types.Choice(['yes', 'no']),
        default='yes'
    )
    if user_response == 'no':
        click.secho("Exiting without generating completions...",
                    color='success', bold=True)
        exit(0)
    subprocess.run([
        f'{shell}', '-c', f'''
        source {completions_funcs_path} && \
            _generate_completion_script && \
                _add_scriptyscripts_completion'''],
        check=True
    )
    click.secho(
        ("Completions generation for scriptyscripts complete!\n"
         "Reload your shell to use the completions."),
        color='success',
        bold=True
    )


if __name__ == '__main__':
    cli()
