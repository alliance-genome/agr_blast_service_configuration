#!/usr/bin/env python 

import json
import yaml

from jsonschema import validate

fh_global_config = open("conf/global.yaml", "r")

fh_global_schema = open("schemas/global_schema.json", "r")

global_config = yaml.safe_load(fh_global_config)
validate_response = validate(global_config, json.load(fh_global_schema))

if validate_response is None:
    print("Global Config Valid format")
else:
    print("Global Config Not Valid Format")
    exit(1)

fh_schema = open("schemas/metadata_schema.json", "r")
schema = json.load(fh_schema)

for data_provider in global_config["data_providers"]:
    data_provider_name = data_provider["name"]
    for environment in data_provider["environments"]:
        print("Validating environment: " + environment)
        config_filename = ".".join(["databases", data_provider_name, environment, "json"])
        config_filepath = "/".join(["conf", data_provider_name, config_filename])
        print("Looking for config file here: " + config_filepath)


        fh_blast_config = open(config_filepath, "r")
        blast_config = json.load(fh_blast_config)

        result = validate(blast_config, schema)

        if result is None:
           print("Valid")
        else:
           print("Not Valid")
           exit(1)
