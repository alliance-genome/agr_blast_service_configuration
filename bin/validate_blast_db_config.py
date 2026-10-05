#!/usr/bin/env python
"""
Validate every BLAST database configuration in this repository.

It used to validate only the provider/environment pairs named in
conf/global.yaml, by building `conf/<provider>/databases.<provider>.<env>.json`
from each pair. That left most of the repository unchecked: global.yaml names
six pairs and there are 36 config files, so 30 were never looked at --
including every file actually deployed. Four WB configs with a `metaData`
typo merged CI-green through that gap, and files like
`databases.SGD_fungal.2024-04-11.json` were unreachable by construction,
because the loop would have looked for them in a `conf/SGD_fungal/` directory
that does not exist.

So this walks conf/ instead. global.yaml is still validated, and is still
what drives a build (`create_blast_db.py -g conf/global.yaml`), but it no
longer decides what gets checked. Two further reports come out of comparing
the two: a pair global.yaml names with no file behind it, and a config file
global.yaml does not name.

Every file is checked before anything exits, so one bad config does not hide
the next.
"""

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft6Validator

CONF = Path("conf")
GLOBAL_CONFIG = CONF / "global.yaml"
GLOBAL_SCHEMA = Path("schemas/global_schema.json")
METADATA_SCHEMA = Path("schemas/metadata_schema.json")


def describe(error) -> str:
    """One line for a jsonschema error, naming where in the document it is."""
    where = "/".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{where}: {error.message}"


def errors_against(validator, document) -> list:
    return [
        describe(e)
        for e in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    ]


def config_files() -> list:
    """Every database config in the repository, in a stable order."""
    return sorted(CONF.glob("*/databases.*.json"))


def pairs_named_by(global_config) -> set:
    return {
        (provider["name"], environment)
        for provider in global_config.get("data_providers", [])
        for environment in provider.get("environments", [])
    }


def pair_for(path: Path):
    """("WB", "WS298") for conf/WB/databases.WB.WS298.json, else None.

    The provider is the directory, not the filename: the filename carries
    variants such as `SGD_fungal` that are not providers and have no
    directory of their own.
    """
    stem = path.name[len("databases.") : -len(".json")]
    provider = path.parent.name
    if stem.startswith(f"{provider}."):
        return provider, stem[len(provider) + 1 :]
    return None


def main() -> int:
    for required in (GLOBAL_CONFIG, GLOBAL_SCHEMA, METADATA_SCHEMA):
        if not required.exists():
            print(f"FAIL  missing {required} -- run this from the repository root")
            return 2

    failures = 0

    global_config = yaml.safe_load(GLOBAL_CONFIG.read_text())
    global_errors = errors_against(
        Draft6Validator(json.loads(GLOBAL_SCHEMA.read_text())), global_config
    )
    if global_errors:
        failures += 1
        print(f"FAIL  {GLOBAL_CONFIG}")
        for e in global_errors:
            print(f"        {e}")
    else:
        print(f"ok    {GLOBAL_CONFIG}")

    metadata_validator = Draft6Validator(json.loads(METADATA_SCHEMA.read_text()))

    files = config_files()
    for path in files:
        try:
            document = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            failures += 1
            print(f"FAIL  {path}")
            print(f"        could not be read as JSON: {e}")
            continue

        file_errors = errors_against(metadata_validator, document)
        if file_errors:
            failures += 1
            print(f"FAIL  {path}  ({len(file_errors)} error(s))")
            for e in file_errors:
                print(f"        {e}")
        else:
            entries = len(document.get("data", []))
            print(f"ok    {path}  ({entries} entries)")

    # global.yaml drives builds, so a pair naming a file that is not there is
    # a broken build waiting to happen. This used to be an uncaught
    # FileNotFoundError part-way through the run.
    named = pairs_named_by(global_config)
    present = {p for p in (pair_for(f) for f in files) if p}
    missing = sorted(named - present)
    if missing:
        failures += 1
        print("\nFAIL  conf/global.yaml names provider/environment pairs with no config file:")
        for provider, environment in missing:
            print(f"        {provider}/{environment}  "
                  f"(expected conf/{provider}/databases.{provider}.{environment}.json)")

    print(f"\n{len(files)} config file(s) checked, {failures} failure(s)")

    # Reported, not failed: a config this repository holds but global.yaml does
    # not name is normal -- most are superseded releases kept for reference.
    # It is worth printing because global.yaml going stale is invisible
    # otherwise, and it has been stale since 2024.
    unnamed = sorted(present - named)
    if unnamed:
        print(
            f"\nnote: {len(unnamed)} config file(s) are not named in global.yaml, so a "
            f"`create_blast_db.py -g` run would not build them:"
        )
        for provider, environment in unnamed:
            print(f"        {provider}/{environment}")

    # Reported separately so that "not named" is not mistaken for "the rest are
    # covered". These filenames carry a variant where the provider goes --
    # SGD_fungal, SGD_test -- and both the validator and the manager build
    # `conf/<provider>/databases.<provider>.<env>.json` from a provider that is
    # also a directory name. So they cannot be named in global.yaml at all, and
    # can only ever be built with `-j <file>`.
    unpaired = [f for f in files if pair_for(f) is None]
    if unpaired:
        print(
            f"\nnote: {len(unpaired)} config file(s) cannot be named in global.yaml, "
            f"because the provider in the filename is not a directory under conf/. "
            f"Build these with `-j <file>`:"
        )
        for path in unpaired:
            print(f"        {path}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
