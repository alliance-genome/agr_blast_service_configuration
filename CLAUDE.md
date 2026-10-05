# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application that validates and manages BLAST database configurations for the Alliance of Genome Resources (AGR). It uses JSON configuration files to define data sources for nucleotide and protein sequences, with a YAML file managing the global database creation process.

## Key Architecture

### Configuration Structure

The project follows a two-level configuration architecture:

1. **Global Configuration** (`conf/global.yaml`): Defines data providers (WB, FB, SGD, XB, ZFIN, ALLIANCE, RGD) and their environments. Each provider can have multiple environment versions (e.g., WB has WS291, WS292).

2. **Provider-Specific Configurations** (`conf/{PROVIDER}/databases.{PROVIDER}.{VERSION}.json`): Each file contains:
   - `data` section: Array of data sources with FASTA file metadata (URIs, md5sums, taxonomic info, sequence types)
   - `metadata` section: Provider information (contact, homepage, logo, release info, public visibility)
   - Optional `genome_browser` section: JBrowse integration details for linking BLAST results to genome browsers

### Schema-Driven Design

- JSON schemas in `schemas/` define the structure for both metadata and global configs
- Python classes are auto-generated from schemas using Quicktype (`src/python/agr_blast_service_configuration/schemas/`)
- Schema validation ensures all configuration files conform to expected formats

### Naming Convention

Configuration files follow strict naming: `databases.{DATA_PROVIDER}.{ENVIRONMENT}.json`
- Example: `databases.WB.WS291.json`, `databases.SGD.2024-06-13.json`

## Common Commands

### Setup and Dependencies
```bash
# Install pre-commit hooks (one-time setup)
poetry run pre-commit install

# Install dependencies
poetry install
```

### Validation
```bash
# Validate all BLAST DB configurations (checks global.yaml and all referenced JSON files)
poetry run python bin/validate_blast_db_config.py

# Run pre-commit checks manually on changed files
poetry run pre-commit run

# Run pre-commit checks on all files
poetry run pre-commit run --all-files
```

### Code Generation
```bash
# Regenerate Python code from JSON schemas (run after schema updates)
./bin/generate_code_from_schemas.sh python
```

### Testing
```bash
# Run tests
poetry run pytest tests/
```

## Important Validation Rules

The pre-commit hook automatically runs `validate_blast_db_config.py` on any JSON file changes in `conf/`. This validation:
1. Validates `conf/global.yaml` against `schemas/global_schema.json`
2. Validates **every** `conf/*/databases.*.json` against `schemas/metadata_schema.json` -- it walks the directory rather than taking its list from `global.yaml`, which previously left 30 of 36 files unchecked
3. Fails if `global.yaml` names a provider/environment pair that has no config file behind it
4. Reports, without failing, which config files `global.yaml` does not name, since those are what a `-g` build would skip
5. Checks every file before exiting, so one bad config does not mask another, and exits non-zero if any failed

## Required Fields in Configuration Files

### Data Section (each entry)
- `uri`: FTP link to FASTA file (required)
- `genus`, `species`: Taxonomic classification (required)
- `md5sum`: File integrity checksum (required)
- `seqtype`: "nucl" or "prot" (required)
- `taxon_id`: NCBI taxon ID (required)
- `blast_title`, `description`, `version`: Descriptive metadata (required)

### Metadata Section
- `dataProvider`, `release`: Provider and version info (required)
- `contact`: Email address (required)
- `homepage_url`, `logo_url`: URLs for web interface (required)
- `dateProduced`: ISO 8601 datetime (required)
- `public`: Boolean controlling visibility (optional)

## Workflow for Adding New Configurations

1. Add new environment to `conf/global.yaml` under appropriate provider
2. Create corresponding JSON file in `conf/{PROVIDER}/` following naming convention
3. Validation runs automatically via pre-commit hook, or run manually with `poetry run python bin/validate_blast_db_config.py`
4. If schemas change, regenerate Python code with `./bin/generate_code_from_schemas.sh python`
