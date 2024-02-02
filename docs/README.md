Sure, here's the documentation in Markdown format:

```markdown
# Creating a JSON Configuration File for Blast Service

The JSON configuration file for the Blast service consists of two main sections: `data` and `metadata`.

## Data Section

The `data` section is an array of objects, each representing a data source. Each object should have the following properties:

- `uri`: The URI where the data source can be accessed.
- `bioproject`: The BioProject ID associated with the data source.
- `blast_title`: A title for the data source.
- `description`: A description of the data source.
- `genus`: The genus of the organism associated with the data source.
- `md5sum`: The MD5 checksum of the data source file.
- `seqtype`: The type of sequences in the data source (e.g., "nucl" for nucleotide sequences, "prot" for protein sequences).
- `species`: The species of the organism associated with the data source.
- `taxon_id`: The taxon ID of the organism associated with the data source.
- `version`: The version of the data source.

## Metadata Section

The `metadata` section is an object that should have the following properties:

- `contact`: The contact information for the data provider.
- `homepage_url`: The URL of the data provider's homepage.
- `logo_url`: The URL of the data provider's logo.
- `dataProvider`: The name of the data provider.
- `dateProduced`: The date when the data was produced.
- `release`: The release version of the data.

Here is an example of a JSON configuration file:

```json
{
  "data": [
    {
      "uri": "ftp://ftp.ebi.ac.uk/pub/databases/wormbase/releases/WS286/species/c_angaria/PRJNA51225/c_angaria.PRJNA51225.WS286.genomic.fa.gz",
      "bioproject": "PRJNA51225",
      "blast_title": "C. angaria Genome Assembly",
      "description": "Caenorhabditis angaria genome assembly",
      "genus": "Caenorhabditis",
      "md5sum": "75552d2bb2012f7f6f11236bb001fba9",
      "seqtype": "nucl",
      "species": "angaria",
      "taxon_id": "NCBITaxon:860376",
      "version": "WS286"
    },
    ...
  ],
  "metadata": {
    "contact": "help@wormbase.org",
    "homepage_url": "https://wormbase.org",
    "logo_url": "https://wormbase.org/img/logo/logo_wormbase_gradient.svg",
    "dataProvider": "WB",
    "dateProduced": "2022-08-09T13:08:22+01:00",
    "release": "WS286"
  }
}
```

Please replace the `...` in the `data` array with additional data source objects as needed.
```
