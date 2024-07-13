import shlex
import itertools
import click
import os
import sys
from pathlib import Path
from difflib import get_close_matches
import subprocess


#: path to ~/scriptyscripts
pth = Path(os.getenv("HOME")).joinpath("scriptyscripts")


@click.group()
def cli():
    pass


@cli.command("path")
def print_path():
    """print the scriptyscriptys path (should be ~/scriptyscripts)."""
    click.secho(str(pth.absolute().resolve()))

    
def get_matches(ctx, param, value, n=1, cutoff=0.1):
    command = value
    results = search_scriptyscripts(ctx, None, '*')
    match = None
    if n <= 0:
        n = len(results)
    matches = get_close_matches(command, results, n=n, cutoff=cutoff)
    if isinstance(matches, str):
        matches = [matches, ]
    if len(matches) == 0:
        click.secho(f"No scriptyscripts command matching '{command}' was found.", err=True)
    if n == 1:
        #: ! handle a single result
        return matches[0]
    else:
        return matches


def search_scriptyscripts(ctx, param, value, n=-1, cutoff=0.1):
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
    results = [str(r) for r in itertools.filterfalse(lambda r: str(r)[-1] == '~', results)]
    if len(results) == 0:
        results = get_matches(ctx, param, value, n=n, cutoff=cutoff)
    return results


@cli.command()
@click.argument("glob_pattern", nargs=-1, callback=search_scriptyscripts)
@click.option("-n", "--n", "--N", default=10, help="Maximum number of results to show")
@click.pass_context
def list(ctx, glob_pattern, n):
    """List the commands in ~/scriptyscripts matching GLOB_PATTERN.
    
    GLOB_PATTERN is a regex-like search pattern, e.g. 'test-*'.
    """
    click.secho('\n')
    results = [g for g in reversed(glob_pattern)]  # ! after callback
    if len(results) == 0:
        click.secho("failed to find any matching commands!", err=1)
    if ctx.obj['_orig.glob_pattern'] == '*':
        for res in results:
            click.secho(res)
        return True
    if len(results) > 5:
        for res in results[:-5]:
            click.secho(res)
        for res in results[-5:]:
            click.secho(res, fg='blue', bold=True)
    click.secho('\n' + results[-1] + '\n', fg='green', bold=True, blink=True)
    click.secho('\n')


@cli.command()
@click.argument("command", nargs=1, required=True, type=click.types.StringParamType(),
                callback=get_matches)
@click.argument("args", nargs=-1, required=False)
def run(command, args):
    """"Execute the given COMMAND (should match something in the ~/scriptyscripts directory).
    
    COMMAND given command in the ~/scriptyscripts directory.
    ARGS arguments for the given command (if needed).
    """
    if args is None:
        args = []
    subprocess.run(shlex.split(command) + args)


@cli.command()
@click.argument("command", nargs=1, required=False, type=click.types.StringParamType(),
                callback=get_matches)
def edit(command):
    """Edit the specified command in emacs.

    COMMAND given command in the ~/scriptyscripts directory.

    ...otherwise opens emacs in the ~/scriptyscripts directory.
    """
    if command is None:
        command = '~/scriptyscripts'
    subprocess.run(shlex.split(f'emacs -f {command}'))


if __name__ == '__main__':
    cli()
