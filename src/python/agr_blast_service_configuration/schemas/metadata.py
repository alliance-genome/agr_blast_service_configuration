from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, List, Optional, Type, TypeVar, cast

import dateutil.parser

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


class GenomeBrowseType(Enum):
    JBROWSE = "jbrowse"
    JBROWSE2 = "jbrowse2"


@dataclass
class GenomeBrowser:
    assembly: str
    data_url: str
    gene_track: str
    mod_gene_url: str
    tracks: List[str]
    type: GenomeBrowseType
    url: str

    @staticmethod
    def from_dict(obj: Any) -> "GenomeBrowser":
        assert isinstance(obj, dict)
        assembly = from_str(obj.get("assembly"))
        data_url = from_str(obj.get("data_url"))
        gene_track = from_str(obj.get("gene_track"))
        mod_gene_url = from_str(obj.get("mod_gene_url"))
        tracks = from_list(from_str, obj.get("tracks"))
        type = GenomeBrowseType(obj.get("type"))
        url = from_str(obj.get("url"))
        return GenomeBrowser(
            assembly, data_url, gene_track, mod_gene_url, tracks, type, url
        )

    def to_dict(self) -> dict:
        result: dict = {}
        result["assembly"] = from_str(self.assembly)
        result["data_url"] = from_str(self.data_url)
        result["gene_track"] = from_str(self.gene_track)
        result["mod_gene_url"] = from_str(self.mod_gene_url)
        result["tracks"] = from_list(from_str, self.tracks)
        result["type"] = to_enum(GenomeBrowseType, self.type)
        result["url"] = from_str(self.url)
        return result


class BlastDBType(Enum):
    """NCBI types for BLAST databases.Taken from the dbtype flag of the makeblastdb command line
    tool.
    """

    NUCL = "nucl"
    PROT = "prot"


@dataclass
class SequenceMetadata:
    """BLAST database metadata."""

    blast_title: str
    description: str
    genus: str
    md5_sum: str
    species: str
    taxon_id: str
    uri: str
    version: str
    bioproject: Optional[str] = None
    genome_browser: Optional[GenomeBrowser] = None
    seqcol_type: Optional[str] = None
    seqtype: Optional[BlastDBType] = None

    @staticmethod
    def from_dict(obj: Any) -> "SequenceMetadata":
        assert isinstance(obj, dict)
        blast_title = from_str(obj.get("blast_title"))
        description = from_str(obj.get("description"))
        genus = from_str(obj.get("genus"))
        md5_sum = from_str(obj.get("md5sum"))
        species = from_str(obj.get("species"))
        taxon_id = from_str(obj.get("taxon_id"))
        uri = from_str(obj.get("uri"))
        version = from_str(obj.get("version"))
        bioproject = from_union([from_none, from_str], obj.get("bioproject"))
        genome_browser = from_union(
            [GenomeBrowser.from_dict, from_none], obj.get("genome_browser")
        )
        seqcol_type = from_union([from_none, from_str], obj.get("seqcol_type"))
        seqtype = from_union([BlastDBType, from_none], obj.get("seqtype"))
        return SequenceMetadata(
            blast_title,
            description,
            genus,
            md5_sum,
            species,
            taxon_id,
            uri,
            version,
            bioproject,
            genome_browser,
            seqcol_type,
            seqtype,
        )

    def to_dict(self) -> dict:
        result: dict = {}
        result["blast_title"] = from_str(self.blast_title)
        result["description"] = from_str(self.description)
        result["genus"] = from_str(self.genus)
        result["md5sum"] = from_str(self.md5_sum)
        result["species"] = from_str(self.species)
        result["taxon_id"] = from_str(self.taxon_id)
        result["uri"] = from_str(self.uri)
        result["version"] = from_str(self.version)
        if self.bioproject is not None:
            result["bioproject"] = from_union([from_none, from_str], self.bioproject)
        if self.genome_browser is not None:
            result["genome_browser"] = from_union(
                [lambda x: to_class(GenomeBrowser, x), from_none], self.genome_browser
            )
        if self.seqcol_type is not None:
            result["seqcol_type"] = from_union([from_none, from_str], self.seqcol_type)
        if self.seqtype is not None:
            result["seqtype"] = from_union(
                [lambda x: to_enum(BlastDBType, x), from_none], self.seqtype
            )
        return result


@dataclass
class Metadata:
    """Top level Alliance BLAST database metadata section."""

    contact: str
    data_provider: str
    date_produced: datetime
    homepage_url: str
    logo_url: str
    release: str
    public: Optional[bool] = None
    """Is this data publicly displayed?"""

    @staticmethod
    def from_dict(obj: Any) -> "Metadata":
        assert isinstance(obj, dict)
        contact = from_str(obj.get("contact"))
        data_provider = from_str(obj.get("dataProvider"))
        date_produced = from_datetime(obj.get("dateProduced"))
        homepage_url = from_str(obj.get("homepage_url"))
        logo_url = from_str(obj.get("logo_url"))
        release = from_str(obj.get("release"))
        public = from_union([from_bool, from_none], obj.get("public"))
        return Metadata(
            contact,
            data_provider,
            date_produced,
            homepage_url,
            logo_url,
            release,
            public,
        )

    def to_dict(self) -> dict:
        result: dict = {}
        result["contact"] = from_str(self.contact)
        result["dataProvider"] = from_str(self.data_provider)
        result["dateProduced"] = self.date_produced.isoformat()
        result["homepage_url"] = from_str(self.homepage_url)
        result["logo_url"] = from_str(self.logo_url)
        result["release"] = from_str(self.release)
        if self.public is not None:
            result["public"] = from_union([from_bool, from_none], self.public)
        return result


@dataclass
class AgrBlastDatabases:
    data: List[SequenceMetadata]
    metadata: Metadata

    @staticmethod
    def from_dict(obj: Any) -> "AgrBlastDatabases":
        assert isinstance(obj, dict)
        data = from_list(SequenceMetadata.from_dict, obj.get("data"))
        metadata = Metadata.from_dict(obj.get("metadata"))
        return AgrBlastDatabases(data, metadata)

    def to_dict(self) -> dict:
        result: dict = {}
        result["data"] = from_list(lambda x: to_class(SequenceMetadata, x), self.data)
        result["metadata"] = to_class(Metadata, self.metadata)
        return result


def agr_blast_databases_from_dict(s: Any) -> AgrBlastDatabases:
    return AgrBlastDatabases.from_dict(s)


def agr_blast_databases_to_dict(x: AgrBlastDatabases) -> Any:
    return to_class(AgrBlastDatabases, x)
