# BLAST database configuration reference

Every BLAST database the Alliance serves exists because a JSON object in this
repository said it should. The object names a FASTA file, pins its checksum,
and supplies the strings that become the on-disk directory path, the BLAST
database title, the tree grouping in the search form, and the genome browser
link on a hit. Nothing downstream re-derives any of that from the sequence
data, so a wrong string here is served as truth until somebody notices.

Two programs read these files, and they read them at different times for
different reasons.

`agr_blastdb_manager` reads a config at build time
(`src/create_blast_db.py`). It downloads each `uri`, verifies it against
`md5sum`, decides a directory from `seqcol_type` or `genus`/`species`, runs
`makeblastdb`, and then — this is the part that surprises people — copies the
config file it was given to `<MOD>/<environment>/environment.json` in the
deploy directory, verbatim (`src/utils.py:38-54`). The build input becomes the
deployment's description of itself.

`agr_sequenceserver` reads that deployed copy at request time, never this
repository. `lib/sequenceserver/routes.rb:270` loads
`public/environments/<mod>/<release>/environment.json` to decorate a report
with genome browser links, and `routes.rb:687` loads the same file again to
attach an organism name to each database for the gene search box. The two
copies can and do differ; see the drift table below.

## File naming

```
conf/<MOD>/databases.<MOD>.<RELEASE>.json
```

The MOD directory and the second dot-field are expected to agree, and three
separate pieces of code depend on the convention:

- `bin/validate_blast_db_config.py:52-55` joins `databases`, the provider name
  from `conf/global.yaml`, the environment string, and `json`, then looks for
  the result under `conf/<provider>/`. A file whose name does not match that
  construction is simply never validated.
- `agr_blastdb_manager/src/create_blast_db.py:468-471` builds that path when the
  manager is driven by `-g conf/global.yaml`; `:414-417` builds the same name
  for the `-l` listing, which only prints what it finds.
- When driven by `-j <path>` instead, the manager recovers the MOD from the
  *filename* — `src/utils.py:403-432` splits on `.` and takes field 1, with a
  prefix match so that `SGD_test` and `SGD_fungal_test` both resolve to `SGD`.
  The environment comes from `-e` and is unrelated to the filename.

That last point is why `<RELEASE>` in the filename is not the directory the
databases land in. The release token is documentation; `-e` is the thing that
decides. The prefix match is what lets a filename like
`databases.SGD_test.2025-10-07.json` resolve to `SGD` at all; without it field 1
would be `SGD_test`, which is in no MOD list. Commit 5aced62 renamed that file
to `databases.SGD.test.2025-10-07.json`, but not for that reason — it says
plainly what the problem was. Both spellings existed with byte-identical
contents, one tracked and one only in the working tree, so the deployed
`R64-5-1m` configuration was not fully reproducible from the repository and the
two copies could drift apart. Nothing referenced either filename;
`bin/combine_sgd_config.py` takes its input and output paths as arguments.

The CI workflow guesses `-e` from the filename and gets it wrong for any file
whose release token contains a dot. `.github/workflows/create_blast_db.yml`
ends with

```
-e $(basename <file> .json | cut -d'.' -f3)
```

For `databases.WB.WS295.json` that yields `WS295`, which is right. For
`databases.SGD.test.2025-10-07.json` it yields `test`, and for
`databases.SGD_fungal_test.2025-10-11.json` it yields `2025-10-11` — neither of
which is the environment those configs are actually deployed under
(`R64-5-1m` and `R64-5-1f`). The workflow is also capped at
`timeout-minutes: 5`, and the 183-entry SGD build on 2025-10-07 took 242.36
seconds end to end (`agr_blastdb_manager/src/blast_db_creation.log:13746-16216`).
SGD's fungal set is 312 entries.

### What is deployed, and from which file

Matching every deployed `environment.json` on this host against every config in
`conf/` by normalised content:

| Deployed environment | Config it came from | Entries |
|---|---|---|
| `ALLIANCE/prod` | `conf/ALLIANCE/databases.ALLIANCE.prod.json` | 9 |
| `FB/FB2024_02` … `FB/FB2026_03` | the matching `conf/FB/databases.FB.<rel>.json` | 197–200 |
| `FB/FB2025_03B` | identical to `FB2025_03`; no config of its own exists | 200 |
| `RGD/8.3.0` | `conf/RGD/databases.RGD.production.json` | 2 |
| `RGD/rgdtest` | `conf/RGD/databases.RGD.production_new.json` | 9 |
| `SGD/R64-5-1f` | *no exact match* — one entry ahead of `databases.SGD_fungal_test.2025-10-11.json` | 312 |
| `SGD/R64-5-1m` | `conf/SGD/databases.SGD.test.2025-10-07.json` | 183 |
| `WB/WS293` … `WB/WS298` | the matching `conf/WB/databases.WB.<rel>.json` | 61–63 |
| `WB/dev` | `conf/WB/databases.WB.WS291.json` | 61 |
| `WB/prod` | `conf/WB/databases.WB.WS293.json` | 61 |
| `ZFIN/prod`, `ZFIN/zfintest` | `conf/ZFIN/databases.ZFIN.production.json` | 13 |

Two of those rows are drift worth fixing rather than facts to work around.

`SGD/R64-5-1f` differs from the repository in exactly one entry: the deployed
copy has a `genome_browser` block on *S. cerevisiae Coding Sequences* that the
repository config does not. Somebody edited the volume directly. Until that
block is committed, regenerating `R64-5-1f` from this repository would silently
remove a working link.

`RGD/8.3.0` serves nine databases — `GRCr8`, `mRatBN7_2`,
`UTH_Rnor_SHRSP_BbbUtx_1_0`, `F344_StmMcwi`, `Lyon_Normot_Rat_Genome`,
`Dahl_SR_JrHsd`, `Lyon_Hypertensive`, `Genome_assembly_UTH_Rnor_WKY_Bbb_1_1`,
`UTH_Rnor_SHR_Utx_2_0` — while its `environment.json` declares two. The
databases were built from `production_new.json` and the config published was
`production.json`. Seven of the nine therefore have no organism and no browser
block as far as the server is concerned.

## The data section

Each element of `data` describes one BLAST database. The schema is
`schemas/metadata_schema.json:84-155`, with `additionalProperties: false`, so a
key not listed there is a validation error rather than a harmless annotation.

| Field | Required by schema | Consumed by |
|---|---|---|
| `uri` | yes | the build, to download; the server, as the join key for `genome_browser` |
| `blast_title` | yes | the build, as the directory name and `makeblastdb -title`; the server, to attach an organism |
| `md5sum` | yes | the build, as an integrity pin |
| `genus` | yes | the build, as a path segment when `seqcol_type` is absent; the server, for the organism string |
| `species` | yes | as `genus` |
| `taxon_id` | yes | the build, as `makeblastdb -taxid` |
| `description` | yes | nothing |
| `version` | yes | nothing reachable |
| `seqtype` | no (defaults to `nucl`) | the build, as `makeblastdb -dbtype` and to pick the residue alphabet |
| `seqcol_type` | no | the build, as the single top-level path segment |
| `bioproject` | no | nothing |
| `genome_browser` | no | the server, to build JBrowse and gene links |

"Consumed by nothing" is a statement about these two repositories, checked by
grep. `description` and `bioproject` appear in no code path at all.
`version` appears in one place, `agr_blastdb_manager/src/utils.py:450`, inside
`edit_fasta`, which no build path calls — only two property tests do
(`tests/unit/test_utils_properties.py:161`, `:179`). They are still worth
filling in correctly —
they are the only record of what a FASTA was — but do not expect changing them
to change anything that is served.

### blast_title

This is the most load-bearing string in the file, and the only one whose exact
spelling is depended upon by two independent programs that never talk to each
other.

The build sanitises it with `re.sub(r"\W+", "_", title).strip("_")`
(`create_blast_db.py:82-83`) and uses the result twice: as the leaf directory
the database files are written into (`:90`, `:94`, `:98-100`) and as
`makeblastdb -title` (`:306`). So the title SequenceServer reads out of the
BLAST database with `blastdbcmd` is the sanitised string, not the original.

The server re-derives the same string from the config independently.
`routes.rb:692` applies `gsub(/\W+/, '_').gsub(/\A_|_\z/, '')` — the Ruby
transliteration of the same regex — and uses it as a key to look up
`"#{genus} #{species}"`:

```ruby
title = entry['blast_title'].to_s.gsub(/\W+/, '_').gsub(/\A_|_\z/, '')
organism = [entry['genus'], entry['species']].compact.join(' ').strip
map[title] = organism unless organism.empty?
```

That join exists because a BLAST database carries no organism of its own. Its
tree categories are the directory grouping, which on SGD's fungal set is a
clade such as `Agaricomycetes_mushrooms_allies` rather than a species, so the
gene search box has nothing to label a result with unless the config supplies
it. Changing a `blast_title` without rebuilding breaks the join on one side
only: the directory and the BLAST title keep the old spelling, the config
carries the new one, the keys stop matching, and the affected databases lose
their organism label with no error anywhere.

Two titles that sanitise to the same string collide, and ZFIN has such a pair.
`conf/ZFIN/databases.ZFIN.production.json` lists `ZFIN TALEN Sequences`
twice, once for `talen_fasta.fa.gz` and once for `zfin_mrph.fa.gz`
(morpholinos). Both resolve to the directory
`Danio/rerio/ZFIN_TALEN_Sequences/`, and on this host that directory holds only
`zfin_mrph.fa.*`. Nothing overwrote anything: the two entries derive different
database file names, so both would have sat side by side in the shared
directory under the same title. The TALEN database was never built, or did not
survive. What the collision guarantees is the shared directory and the
duplicate tree label — the morpholino database is served under the TALEN label.
Nothing in the pipeline reports either the duplicate title or the missing
database.

ZFIN is short of databases for other reasons too: thirteen entries are
declared, eight directories exist, one of them
(`Published_Zebrafish_Proteins/`) is empty, and seven databases are actually
served.

### uri

The `uri` is both the download source and, at report time, the key that
attaches a `genome_browser` block to a hit — and it is a substring match, not
an identity.

`blast/hit.rb:83-85` works out a `species_identifier` from the database file on
disk: basename, drop the extension, drop a trailing `db`. `hit.rb:116` then
walks the config in order and takes the first entry whose `uri` *contains* that
string. Checked against the deployed data on this host, that match is almost
never unique:

| Environment | Databases | Config entries matched per database |
|---|---|---|
| `SGD/R64-5-1f` | 312 | 1 for all 312 |
| `ZFIN/prod` | 7 | 1 for all 7 |
| `FB/FB2026_03` | 200 | 3 for 195 of them, 1 for 5 |
| `WB/WS298` | 63 | 2 for 54, 4 for 4, 5 for 5 |

The three-way matches in the FlyBase row are the RefSeq species, whose genomic,
RNA and protein FASTAs all live under one `GCF_` accession directory — the
`species_identifier` is the bare accession `GCF_009650485`, so all three
databases match all three entries and the first in file order wins. In practice
this means a `genome_browser` block attaches per species, not per database.
That is usually what was wanted, and occasionally not: WormBase builds its
protein and genomic databases both as `c_elegansdb` under `PRJNA13758`, the
protein database matched the genomic entry, inherited its `genome_browser`
block, and produced browser links at amino-acid offsets. The fix was a
`locatable` gate (`hit.rb:105-106`) rather than a better join, plus a hardcoded
exception for `c_elegans` at `hit.rb:114-115`.

The URI basename also decides the database filename, via
`fasta_file.replace(''.join(Path(fasta_file).suffixes), 'db')`
(`create_blast_db.py:302` and `:307`). `Path.suffixes` treats every dot-separated tail
as a suffix, so `c_elegans.PRJNA13758.WS298.genomic.fa.gz` becomes
`c_elegansdb` and `dmel-all-transcript-r6.69.fasta.gz` becomes
`dmel-all-transcript-r6db` — the version number is eaten. Deployed ZFIN
databases are named `ensembl_zf.fa.*`, which the current code would not
produce, so that derivation has changed at least once; do not rely on being
able to predict the filename from the URI across releases.

### md5sum

`md5sum` is a pin on the bytes, not a description of them. The build downloads
the URI, hashes the file whole with `hashlib.md5` (`utils.py:364-400`), and
refuses the entry if the digest differs. There is no "update the checksum
automatically" path, by design: a changed digest means the file behind a stable
URL has been replaced, and that is something a person should look at.

A mismatch fails **the entry**, not the run. `process_entry` returns `False`,
`process_json_entries` records a failure, carries on, and ends by returning
`successful > 0` (`create_blast_db.py:875`) — but nothing checks that value.
`process_files` is called purely for its side effects (`:1072`, `:1085`), and
the only `sys.exit(1)` in the file is the outer exception handler (`:1307`), so
the run exits 0 whether one entry failed or every one of them did. That is the
mechanism behind the ALLIANCE
build failure of 2024-10-09: entry 1, *C. elegans*, failed on
`MD5sums do not match`; entry 2, zebrafish, built; the disk filled during entry
3 and entries 3 through 9 failed in under two seconds each; the run reported
`create_dbs function completed in 65.78 seconds` and exited 0. A year later the
one database that existed was copied to production, and `environment.json` —
the input config, all nine genomes — was published alongside it. `/blast/ALLIANCE/prod/`
has declared nine genomes and served one ever since. The full account is
`agr_blastdb_manager/docs/alliance_2024_build_failure.md`; the repair plan is
`agr_sequenceserver/docs/ALLIANCE_WIDE_PLAN.md`.

Re-verified on 2026-09-30, eight of those nine checksums still match what Adam
recorded in 2024. Only *C. elegans* is genuinely stale
(configured `4af7b125bde3c80617ad846cc2ff266e`, actual
`5c0d5cae0c4cd14a05fcf9e3092c4597`), and that entry still claims
`version: WS292`, so it probably wants a new URI rather than a new digest.

To get a digest for a new entry, stream it rather than keeping a copy:

```shell
curl -sL "<uri>" | md5sum
```

Verified against a real entry — `Sc_nuclear_chr.fsa.gz` hashes to
`6e17f7ebcacb819e44cd593f5e0b636c`, which is what
`conf/SGD/databases.SGD.test.2025-10-07.json` declares.

Two escapes exist and both should be used knowingly. `--skip-md5-check`
(defined at `create_blast_db.py:1012`) disables verification for a whole run, in
both download helpers (`utils.py:1073-1075` in `get_files_http`, `:1205-1209`
in `get_files_ftp`), and ZFIN is exempt unconditionally
(`utils.py:1076-1078`, `:1210-1214`) because its download
URLs do not serve stable bytes. ZFIN's `md5sum` values are therefore decorative
— they are still required by the schema, and nothing checks them.

### seqcol_type, genus and species: the directory layout

`create_db_structure` (`create_blast_db.py:62-120`) picks one of three layouts,
in this order:

```python
if "seqcol_type" in config_entry:
    db_path = f".../databases/{sanitized_seqcol_type}/{sanitized_blast_title}/"
elif "seqcol" in config_entry:
    db_path = f".../databases/{config_entry['seqcol']}/{sanitized_blast_title}/"
else:
    db_path = f".../databases/{genus}/{species}/{sanitized_blast_title}/"
```

This matters beyond tidiness, because the search form's tree is built from the
directory path and nothing else. `makeblastdb.rb:339-344` takes the path of
each database relative to the environment's `databases/` directory, splits it,
and drops the last component:

```ruby
def get_categories(path)
  db_dir = @database_dir.end_with?('/') ? @database_dir : "#{@database_dir}/"
  relative = path.sub(db_dir, '')
  parts = relative.split('/').reject(&:empty?)
  parts[0..-2]
end
```

The component dropped is the database *file* name, so the sanitised
`blast_title` directory is itself a grouping level rather than the leaf. That
means `seqcol_type` produces two grouping levels — the clade, then the
sanitised `blast_title` — and `genus`/`species` produces three; the database
hangs below the last of them, making the trees three and four nodes deep
respectively. Measured on the running test instance,
`/blast/SGD/R64-5-1f/searchdata.json` gives all 312 databases two categories
(`["Agaricomycetes_mushrooms_allies", "M_oreades_Coding_Sequences"]`) and
`/blast/WB/WS298/searchdata.json` gives all 63 three (`["Brugia", "malayi",
"B_malayi_Genome_Assembly"]`). Both layouts are visible on this host:

```
WB/WS298/databases/Caenorhabditis/elegans/C_elegans_Genome_Assembly/c_elegansdb.*
SGD/R64-5-1f/databases/Candida/C_albicans_Genome_Assembly/*
```

`seqcol_type` was introduced so SGD could group by clade instead of by
taxonomy, since a 312-database fungal set grouped by genus is unusable. It is
free text and is sanitised the same way as `blast_title`, so
`"S288C Reference Strain|Genomic DNA"` becomes the directory
`S288C_Reference_Strain_Genomic_DNA`. Only three configs use it, all SGD:
`databases.SGD.test.2025-10-07.json` (183 entries),
`databases.SGD.2025-10-03_combined.json` (183) and
`databases.SGD_fungal_test.2025-10-11.json` (312).
`bin/combine_sgd_config.py` is the script that produced them, by moving
descriptive strings out of `genus`/`species` into `seqcol_type` and restoring
real taxonomy. It is currently untracked.

`seqcol` — the second branch above — is dead. No config in this repository uses
it, and because `schemas/metadata_schema.json:86` sets
`additionalProperties: false` and lists no `seqcol`, any config that did use it
would fail validation. Treat the branch as history.

When `seqcol_type` is absent, `genus` and `species` go into the path verbatim,
unsanitised. That is why the ALLIANCE config's misspellings matter: it has two
*Xenopus* entries spelled `xenupus` and `xenupos`, which a complete build would
render as two separate misspelled genera in the tree. Seven of its nine genera
are lowercase, those two among them; only `Caenorhabditis` and `Danio` are
capitalised, and *Danio* is the only one that has ever been built.

### seqtype and taxon_id

`seqtype` is `nucl` or `prot` and reaches `makeblastdb -dbtype` directly
(`create_blast_db.py:305`). It also selects the residue alphabet that
`deduplicate_fasta` uses to decide whether a duplicate record is corrupt
(`create_blast_db.py:123-126`), which is how the FlyBase transcript 6.69
problem is now handled. The schema gives it a default of `nucl`
(`metadata_schema.json:119-126`) and does not require it; every entry in the
repository sets it anyway.

`taxon_id` is interpolated into `makeblastdb -taxid` after stripping a
`NCBITaxon:` prefix (`create_blast_db.py:308`), so both `NCBITaxon:7955` and a
bare `7955` work. Usage is split roughly in half across the repository — 2,574
prefixed against 2,194 bare of the 4,768 entries — but the split follows the era
of the file, not the MOD. WormBase, ZFIN, RGD, ALLIANCE and SGD's fungal configs
are prefixed throughout; FlyBase from `FB2024_02` on, Xenbase, and SGD's 2025
183-entry configs — including the deployed `databases.SGD.test.2025-10-07.json` —
are bare. `databases.FB.FB2022_04.json` is prefixed for all 122 of its entries,
and `databases.SGD.2024-06-06.json` mixes both in one file, 134 prefixed and 49
bare. So you cannot infer the form from the MOD; look at the file. An empty or
malformed value is fatal — ALLIANCE's `mus musculus` entry carries
`taxon_id: "NCBITaxon:"`, which interpolates to nothing and makes
`makeblastdb` exit 1, so mouse cannot build even with disk available.

## The metadata section

`metadata` is required by the schema (`metadata_schema.json:19-22`) and is read
by neither the manager nor the server at runtime. One consumer exists but never
runs: `agr_sequenceserver/public/resource_logo.js:2-3` fetches the deployed
`environment.json` and uses `metadata.homepage_url` and `metadata.logo_url` to
build a navbar logo link — and its script tag has been commented out at
`views/layout.erb:156`, so nothing loads it. `agr_blastdb_manager` reads none of
these fields at all. The page chrome they look like they drive is actually driven
by a separate, hand-maintained file at the root of the deployed config volume,
`environment_info.json`, which holds the same fields per MOD per release plus a
`display_name` that exists in no schema. It is served at
`/blast/environment_info.json` (`routes.rb:134-145`); nothing in
`agr_sequenceserver` fetches it, so whatever consumes it lives elsewhere and I
have not confirmed what.

Fill `metadata` in anyway, for the same reason as `description`: it is the
record. But a wrong `release` or a missing `public: false` changes nothing that
is served today.

Four WormBase configs spell the section `metaData` instead of `metadata`:
`WS293`, `WS294`, `WS295` and `WS296`. `WS297` and `WS298` spell it correctly.
Nothing broke, because nothing reads the section — but all four fail schema
validation, which is covered below.

## genome_browser

A `genome_browser` block turns a hit into one or more outbound links. It is
optional, and sparse: 276 of the 4,768 data entries in the repository carry
one. Nearly all of them are on nucleotide entries — 275 of the 276. The one
exception is deliberate: commit 5bc9697 gave SGD's *Protein sequences* entry in
`databases.SGD.test.2025-10-07.json` a `jbrowse2` block, because SGD names the
gene's location in its protein deflines in the same form as its ORF ones, so
`hit.rb`'s `locatable` gate can place the hit at its whole gene. That file is
the config `SGD/R64-5-1m` is served from, so it is a deployed protein block, not
a leftover.

WormBase puts one on 31 of the 32 nucleotide entries in WS298 — the exception is
*S. hermaphroditum CDS Sequences* — and on all 31 in every earlier release from
WS291 on. FlyBase puts one on exactly one entry out of 200, *D. melanogaster Genome
Assembly 6.69*, and only that one database gets a JBrowse link. Each of
FlyBase's five *D. melanogaster* FASTAs has its own URI stem
(`dmel-assembly`, `dmel-transcript`, `dmel-translation`, `dmel-intergenic`,
`dmel-transposon`), so each matches exactly one config entry and a transcript or
protein hit never reaches the assembly's block. Replaying `hit.rb:83-116` over
the deployed `FB/FB2026_03` data confirms it: of the 200 built databases,
`dmel-assemblydb` is the only one whose first matching entry carries a
`genome_browser` block. The per-species inheritance described above happens on
WormBase, where every database of a species is named `<species>db` — there 30 of
the 31 protein databases in WS298 resolve to that species' *Genome Assembly*
entry, which is why the `locatable` gate exists.

The schema (`metadata_schema.json:156-211`) requires `type`, `assembly`, `url`,
`tracks`, `gene_track`, `mod_gene_url` and `data_url`. The code does not: the
JBrowse link needs only the first four. The gene lookup runs whenever
`gene_track` is present and the hit is not protein (`hit.rb:130`);
`mod_gene_url` is tested separately (`hit.rb:146`) and only controls the extra
MOD report link. `gene_track` without `data_url` is not a skip but a crash —
`"jbrowse-nclist-cli -b " + nil` raises a `TypeError` at `hit.rb:137`. No
deployed config is in that state, because the blocks missing `data_url` also
lack `gene_track`.

| Field | What the server does with it |
|---|---|
| `type` | `jbrowse` or `jbrowse2`; selects which URL shape to build (`links.rb:441`, `:515`) |
| `url` | base of the link; a `?` already present makes the separator `&` (`links.rb:500`, `:576`) |
| `assembly` | JBrowse 1: `?data=data/<assembly>` (`links.rb:508`). JBrowse 2: `&assembly=<assembly>` and the `assemblyNames` of the injected hit track |
| `tracks` | appended to `&tracks=`, plus `Hits` (JBrowse 1) or `blasthits` (JBrowse 2) |
| `gene_track` | with `data_url`, the NCList track queried by `jbrowse-nclist-cli` to name the gene under the hit (`hit.rb:130-154`) |
| `data_url` | base URL of the NCList data for that lookup |
| `mod_gene_url` | prefixed to the gene id returned by that lookup to make a MOD report link (`links.rb:592-599`) |

Three behaviours are worth knowing before you spend time tuning a block.

The configured `tracks` are ignored for FlyBase under `type: "jbrowse"`:
`links.rb:489-492` overrides them with `["Gene_span", "RNA"]`. This does not
affect FlyBase today, which is on `jbrowse2`.

Query parameters in `url` survive, which is how commit 1d0f2bf added
`tracklist=true` to FlyBase's links with no code change at all. FlyBase's URL
already carries `?config=dmel%2Fconfig.json`, the server notices the `?` and
joins with `&`, and the token simply travels along:

```
https://flybase.org/jbrowse2/?config=dmel%2Fconfig.json&tracklist=true&loc=2L%3A4999001..5001400&tracks=genespan%2CGene%2CRNA%2Cblasthits&...
```

The gene lookup is deliberately off for protein hits even when the block is
present, because feeding amino-acid offsets to a genomic track reports whatever
gene happens to sit at that base pair (`hit.rb:130`). A link is also
suppressed outright when no reference name can be extracted, including when the
accession comes back as `gnl|BL_ORD_ID` (`links.rb:471`, `:563`) — which is the
state ZFIN's GRCz11 database under `ALLIANCE/prod` is in, having been built
without `-parse_seqids`.

Of the 276 blocks in the repository, 272 are `jbrowse2` and 4 are `jbrowse`.
All four JBrowse 1 blocks point at `https://jbrowse.yeastgenome.org/` and sit
in SGD configs that are not deployed; no deployed environment uses JBrowse 1.

## Validating before you commit

The validator is `bin/validate_blast_db_config.py`. It must be run from the
repository root, because it opens `conf/global.yaml` and
`schemas/metadata_schema.json` by relative path (`:25`, `:41`):

```shell
poetry run python bin/validate_blast_db_config.py
```

Both that and a bare `python3 bin/validate_blast_db_config.py` work on this
host and exit 0 against the current tree. Run from anywhere else, it dies with
`FileNotFoundError: conf/global.yaml`. The same command runs in CI
(`.github/workflows/validator.yml`) and as a pre-commit hook scoped to
`^conf/` JSON changes (`.pre-commit-config.yaml`).

Three things about it will bite you.

**It only checks what `conf/global.yaml` names.** The loop at `:45-49` iterates
providers and environments from the global file and constructs a filename for
each. `global.yaml` currently lists six pairs — `WB/WS291`, `WB/WS292`,
`FB/FB2024_04`, `SGD/2024-06-13`, `XB/5.5.1`, `ALLIANCE/prod` — so six of the
36 configs in `conf/` are validated and thirty are not. Validating all 36
against `schemas/metadata_schema.json` directly, ten fail:

| File | Why |
|---|---|
| `conf/WB/databases.WB.WS293.json` through `WS296.json` | `metaData` is not `metadata` |
| `conf/RGD/databases.RGD.production.json`, `production_new.json` | `genome_browser` missing `data_url`, `gene_track`, `mod_gene_url` |
| `conf/SGD/databases.SGD.2025-10-03_combined.json`, `SGD.test.2025-10-07.json`, `SGD_fungal_test.2025-10-11.json`, `SGD_test.2025-10-03.json` | same three `genome_browser` fields |

`SGD.test.2025-10-07.json` and `SGD_fungal_test.2025-10-11.json` are the two
configs SGD is served from. They have been deployed, repeatedly, in a state the
repository's own schema rejects — because `global.yaml` does not name them, so
nothing ever asked.

`global.yaml` last had a content change on 2024-09-29 (commit d7c849d). Part of
why it drifts is mechanical: `.github/workflows/flybase.yml` does
`perl -pi -e 's/FB\d{4}_\d{2}/<new release>/' global.yaml` and then opens a PR
with `add-paths: "conf/FB/*.json"`, which excludes `conf/global.yaml`. The edit
is made and never committed.

**Adding RGD to `global.yaml` will fail.** `schemas/global_schema.json:27-34`
enumerates `WB`, `SGD`, `XB`, `FB`, `ZFIN`, `ALLIANCE`. `RGD` is not in the
list, although `conf/RGD/` has existed since 2025 and the manager's own MOD list
includes it (`agr_blastdb_manager/src/utils.py:35`). The enum needs `RGD` added
before the RGD configs can be covered.

**`format` keywords are not enforced.** The script calls
`jsonschema.validate(instance, schema)` with no `format_checker`, so
`"format": "uri"`, `"format": "email"` and `"format": "date-time"` are
decorative. A `uri` of `this is not a uri`, a `contact` of `not an email` and a
`dateProduced` of `not a date` all pass. SGD's `dateProduced: "2025-10-07"` is
a date, not a date-time, and passes for the same reason.

On failure the script does not print "Not Valid" and exit 1 as its structure
suggests — `validate()` raises, so the else-branches at `:36-38` and `:70-72`,
the ones that print "Not Valid" and exit 1, are unreachable. The `if` branches
above them are what run on a successful pass, printing "Global Config Valid
format" (`:34-35`) and "Valid" (`:68-69`). What you get instead is an uncaught
`ValidationError`, exit code
1, and a traceback that includes the entire offending instance. For a WormBase
config that is roughly 60 KB of output for a one-word error, so read the first
five lines and ignore the rest.

To check a file `global.yaml` does not name, validate it directly:

```shell
python3 - <<'EOF'
import json
from jsonschema import Draft6Validator
schema = json.load(open('schemas/metadata_schema.json'))
config = json.load(open('conf/SGD/databases.SGD.test.2025-10-07.json'))
for e in sorted(Draft6Validator(schema).iter_errors(config), key=lambda e: list(e.path)):
    print(list(e.path), e.message)
EOF
```

`iter_errors` reports every problem rather than aborting on the first, and
prints the JSON pointer instead of the instance.

## Adding a release

1. Produce the config. FlyBase is automated: run the `Update FlyBase
   Configuration` workflow with the release number, which copies
   `flybase/blast-db-configuration`'s `conf/*.json` into `conf/FB/` and opens a
   PR. WormBase and SGD publish machine-readable metadata that
   `agr_blastdb_manager/Makefile` knows how to fetch
   (`ftp.ebi.ac.uk/.../blast_meta.wormbase.json`,
   `www.qa.yeastgenome.org/webservice/sgd_blast_metadata` — the QA host, not
   production). Everything else is by
   hand, usually by copying the previous release's file.
2. Name it `conf/<MOD>/databases.<MOD>.<RELEASE>.json`.
3. Update every `uri`, every `md5sum`, every `version`, and the release string
   inside `genome_browser.data_url` — WormBase's `data_url` embeds the release
   (`.../WormBase/WS298/p_redivivus_PRJNA186477/`), so a copied config will
   silently point gene lookups at the previous release's NCList data.
4. Add the provider and environment to `conf/global.yaml` so the validator
   covers the file. If the provider is RGD, add `RGD` to the enum in
   `schemas/global_schema.json` first.
5. Validate, with the command above and, because `global.yaml` coverage is
   partial, with `iter_errors` against the file you actually changed.
6. Decide the environment name the build will deploy under, and pass it as
   `-e`. It is not read from the filename. If you let the CI workflow infer it,
   check what `cut -d'.' -f3` gives for your filename first.

## Adding a database to an existing release

1. Append an object to `data`. The eight required fields are `uri`,
   `blast_title`, `description`, `genus`, `species`, `md5sum`, `taxon_id` and
   `version`; add `seqtype` explicitly rather than relying on the `nucl`
   default.
2. Get the checksum from the URI itself (`curl -sL <uri> | md5sum`), not from a
   local copy you may have modified.
3. Check that the sanitised `blast_title` is unique within the file.
   `re.sub(r"\W+", "_", title).strip("_")` must not collide with any existing
   entry's, or one database will overwrite the other's directory, as ZFIN's two
   `ZFIN TALEN Sequences` entries do.
4. If the release uses `seqcol_type`, set it; mixing conventions within one file
   produces a tree with some branches three nodes deep and others four.
5. Add a `genome_browser` block only if a browser actually has the assembly. If
   the database is protein, expect the JBrowse link to appear only when deflines
   carry coordinates — SGD's do, WormBase's do not.
6. Validate, commit, and remember that merging the PR triggers
   `.github/workflows/create_blast_db.yml` on the `blast2` runner.

## Repository state to be aware of

Four paths in the working tree are untracked and should not be committed
casually: `CLAUDE.md`, `bin/combine_sgd_config.py` (the script that generated
the three `seqcol_type` SGD configs, so worth tracking deliberately),
`conf/WB/databases.WB.WS291_small.json`, and
`conf/WB/.databases.WB.WS285.json.swp`, which is an abandoned Vim swap file and
should be deleted rather than tracked. 35 of the 36 configs under `conf/` are
tracked.

`agr_blastdb_manager` carries its own `conf/` directory with a 2022-era subset
of these files — `global.yaml` (WB only, everything else commented out),
`FB2022_04`, `SGD/2022-06-22`, `WB/WS285`, `WB/WS286`, `XB/5.5.1`, and a copy of
the same stray `.swp`. Two of the five overlapping JSON files — `FB2022_04` and
`XB 5.5.1` — already differ from this repository's; `SGD/2022-06-22`,
`WB/WS285` and `WB/WS286` are byte-identical. Every real build recorded in that
repo's log reads
`../../agr_blast_service_configuration/conf/...`, the sibling checkout, so the
vendored copy is dead weight that looks authoritative.

The Python classes under `src/python/agr_blast_service_configuration/schemas/`
are generated from the schemas by Quicktype
(`./bin/generate_code_from_schemas.sh python`) and are currently in step with
them — `SequenceMetadata` has `seqcol_type`, `genome_browser` and `bioproject`.
Nothing imports them except `tests/python/test_metadata.py`, which round-trips
a fabricated config through `to_dict`/`from_dict`. Regenerate them when you
change a schema, but do not expect the build or the server to notice.
