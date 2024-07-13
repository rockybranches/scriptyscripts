from setuptools import setup, find_packages

import toml

with open("pyproject.toml") as f:
    pyproject = toml.load(f)


setup(
    name='scriptyscripts',
    version=pyproject["tool"]["poetry"]["version"],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'scriptyscripts = scriptyscripts.cli:cli',
        ],
    },
)