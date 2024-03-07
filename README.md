
## Description

This project is a Python application that validates BLAST database configurations.
It uses JSON configuration files to manage data sources for nucleotide and protein sequences. A YAML file can also be
used to manage the database creation process.

In the bin folder, there is a Python script that validates the JSON configuration files, and it can be used
directly on manuallya or automatically generated JSON files. The validator also checks the global YAML to find the
different JSON files and their respective enviropnments.

The docs folder contains documentation on how to create  these configuration files, with required fields and structures.

## Prerequisites

This repo uses the [pre-commit](https://pre-commit.com/) tool to perform some simple checks and validation before a git commit is executed.
The pre-commit hooks are configued in [.pre-commit-config.yaml](./pre-commit-config.yaml) and the pre-commit tool is installed as a dev dependency in `pyproject.toml`.

### Initial configuration

This only needs to be done once in a repo.

```shell
poetry run pre-commit install
```

### Running checks manually

Run pre-commit hooks on changed files.

```shell
poetry run pre-commit run
```

Run pre-commit hooks on all files
```shell
poetry run pre-commit run --all-files
```

## How to create a JSON configuration file

[Follow this simple guid on what is required on a
JSON configuration file](docs/README.md)

### Executing program

```python
python bin/validate_blast_db_config.py
```

## Authors

Adam Wright and Paulo Nuin with support from the Alliance of Genome Resources
and WormBase

## Version History

* 0.1
    * Initial Release
