#!/usr/bin/env python

import json

import yaml
from jsonschema import validate


def validate_blast_config():
    """
    This function validates the configuration files for the Blast service.

    It first loads and validates the global configuration file against its corresponding schema.
    If the global configuration file is not valid, the function will print an error message and exit with status code 1.

    Then, for each data provider in the global configuration, it validates the configuration file for each environment.
    If any of these configuration files are not valid, the function will print an error message and exit with status code 1.

    If all configuration files are valid, the function will print a success message for each file.

    :return: None
    """

    # Open the global configuration and schema files
    fh_global_config = open("conf/global.yaml", "r")
    fh_global_schema = open("schemas/global_schema.json", "r")

    # Load the global configuration and validate it against the schema
    global_config = yaml.safe_load(fh_global_config)
    validate_response = validate(global_config, json.load(fh_global_schema))

    # If the global configuration is valid, print a success message
    # Otherwise, print an error message and exit the program
    if validate_response is None:
        print("Global Config Valid format")
    else:
        print("Global Config Not Valid Format")
        exit(1)

    # Open the metadata schema file
    fh_schema = open("schemas/metadata_schema.json", "r")
    schema = json.load(fh_schema)

    # For each data provider in the global configuration
    for data_provider in global_config["data_providers"]:
        data_provider_name = data_provider["name"]
        # For each environment of the data provider
        for environment in data_provider["environments"]:
            print(f"Validating environment: {environment}")
            # Construct the filename and filepath of the configuration file
            config_filename = ".".join(
                ["databases", data_provider_name, environment, "json"]
            )
            config_filepath = "/".join(["conf", data_provider_name, config_filename])
            print(f"Looking for config file here: {config_filepath}")

            # Open the configuration file and load it
            fh_blast_config = open(config_filepath, "r")
            blast_config = json.load(fh_blast_config)

            # Validate the configuration against the schema
            result = validate(blast_config, schema)

            # If the configuration is valid, print a success message
            # Otherwise, print an error message and exit the program
            if result is None:
                print("Valid")
            else:
                print("Not Valid")
                exit(1)


if __name__ == "__main__":
    validate_blast_config()
