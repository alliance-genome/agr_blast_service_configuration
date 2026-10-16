#!/usr/bin/env python3
"""
Move SGD's descriptive grouping out of genus/species and into seqcol_type.

SGD's own export puts a tree heading where the taxonomy goes: `genus` reads
"S288C Reference Strain" and `species` reads "Genomic DNA". The server
interpolates genus and species into the on-disk database path, which becomes
the database tree's grouping, so a config in that shape builds directories
named after headings and loses the organism. This script restores
Saccharomyces/cerevisiae and keeps the heading in `seqcol_type`, which
`database_output_dir` prefers over genus/species when present.

Provenance: run once on 2025-10-07 to produce
`conf/SGD/databases.SGD.2025-10-03_combined.json` from
`conf/SGD/databases.SGD_test.2025-10-03.json`. Re-running it on that input
still reproduces the committed output byte for byte, all 183 entries, which is
why the file is worth keeping rather than describing.

**It is not idempotent, and it refuses to run twice.** On a second pass every
entry's genus is already "Saccharomyces", so the fallback branch fires and
rewrites `seqcol_type` to "Saccharomyces|cerevisiae" -- destroying the
grouping that drives the tree, on all 183 entries, with no error. The guard in
transform_config is the only thing standing between that and a config nobody
would notice was flattened until the tree rendered. Give it an SGD export, not
a config this script has already touched.
"""

import json
import sys


def get_taxonomic_info(current_genus, current_species):
    """
    Actual taxonomy, plus the heading to keep.

    Returns (genus, species, seqcol_type). Every recognised branch answers
    Saccharomyces cerevisiae: the strains in this export are all S. cerevisiae
    and the strain name is carried in the heading, not in the species field.
    """
    if current_genus == "S288C Reference (DNA/RNA/Vector)":
        seqcol_type = f"S288C Reference (DNA/RNA/Vector)|{current_species}"
        genus = "Saccharomyces"
        species = "cerevisiae"
    elif current_genus == "S288C Reference Strain":
        seqcol_type = f"S288C Reference Strain|{current_species}"
        genus = "Saccharomyces"
        species = "cerevisiae"
    elif "Alternative Reference Strains" in current_genus:
        # The species field carries the actual strain name here, so the heading
        # is the genus field alone.
        seqcol_type = current_genus
        genus = "Saccharomyces"
        species = "cerevisiae"
    elif "Other Strains" in current_genus or "Other S. cerevisiae Strains" in current_genus:
        seqcol_type = current_genus
        genus = "Saccharomyces"
        species = "cerevisiae"
    else:
        # Nothing recognised. Keeping the input verbatim is the only safe
        # answer, and it is also what makes a second run destructive, which is
        # why transform_config refuses one.
        seqcol_type = f"{current_genus}|{current_species}"
        genus = current_genus
        species = current_species

    return genus, species, seqcol_type


def transform_config(input_file, output_file):
    """Transform the configuration file. Returns an exit status."""

    with open(input_file, "r") as f:
        config = json.load(f)

    already = [e["blast_title"] for e in config["data"] if "seqcol_type" in e]
    if already:
        print(
            f"Refusing to run: {len(already)} of {len(config['data'])} entries "
            f"already carry seqcol_type (e.g. {already[0]!r}), so this has run "
            f"on {input_file} before. A second pass would rewrite every "
            f"seqcol_type to 'Saccharomyces|cerevisiae' and flatten the "
            f"database tree. Start from the SGD export instead.",
            file=sys.stderr,
        )
        return 1

    for entry in config["data"]:
        genus, species, seqcol_type = get_taxonomic_info(
            entry["genus"], entry["species"]
        )
        entry["genus"] = genus
        entry["species"] = species
        entry["seqcol_type"] = seqcol_type

    with open(output_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Transformed configuration written to {output_file}")
    print(f"Total entries: {len(config['data'])}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 combine_sgd_config.py <input_file> <output_file>")
        sys.exit(1)

    sys.exit(transform_config(sys.argv[1], sys.argv[2]))
