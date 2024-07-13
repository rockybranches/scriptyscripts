#!/usr/bin/env sh

poetry version patch && \
poetry install && \
pipx upgrade scriptyscripts



