#!/usr/bin/env bash

set -eE -o pipefail

function run_quicktype_python() {
  local schema_file="$1"
  local out_file="$2"
  local top_level="$3"
  # Quicktype's --python-version flag only supports up to 3.7 currently
  local python_version=${4:-'3.7'}
  npx quicktype --lang python --python-version $python_version -s schema --src $schema_file -o $out_file -t $top_level
}

function gen_python {
  echo "Generating python code..."
  run_quicktype_python schemas/metadata_schema.json src/python/agr_blast_service_configuration/schemas/metadata.py AgrBlastDatabases
  run_quicktype_python schemas/global_schema.json src/python/agr_blast_service_configuration/schemas/global.py Global
  poetry run black src/python
}

function usage {
  echo "Usage: $0 python" >&2
  exit 1
}

case "$1" in
  python)
    gen_python
    ;;
  *)
    usage
    ;;
esac
