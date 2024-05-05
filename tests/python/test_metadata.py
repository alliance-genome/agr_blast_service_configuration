import json
import sys

import agr_blast_service_configuration.schemas.metadata as agr_db


class TestMetadataInstance:
    sequence_metadata = [
        {
            "blast_title": "Test DB 1",
            "description": "Test DB 1",
            "genus": "Genus1",
            "species": "species1",
            "taxon_id": "9999999",
            "md5sum": "thisisafakechecksum",
            "uri": "http://foo/db.fasta",
            "version": "1.0",
            "seqtype": "nucl",
        },
        {
            "blast_title": "Test DB 2",
            "description": "Test DB 2",
            "genus": "Genus2",
            "species": "species2",
            "taxon_id": "9999999",
            "md5sum": "thisisafakechecksum",
            "uri": "http://bar/db.fasta",
            "version": "2.0",
            "seqtype": "prot",
        },
    ]
    metadata = {
        "contact": "John Smith",
        "dataProvider": "AwesomeBase",
        "dateProduced": "2024-05-04T00:00:00",
        "homepage_url": "http://awesomebase.org",
        "logo_url": "http://awesomebase.org/logo.png",
        "release": "v1.0",
        "public": True,
    }

    def test_agr_blast_databases(self):
        data = [
            agr_db.SequenceMetadata.from_dict(seq_md)
            for seq_md in self.sequence_metadata
        ]
        metadata = agr_db.Metadata.from_dict(self.metadata)
        db = agr_db.AgrBlastDatabases(data, metadata)
        assert db is not None
        for idx, orig_md in enumerate(self.sequence_metadata):
            db_data = db.data[idx].to_dict()
            for key, value in orig_md.items():
                assert db_data.get(key) == value

        for key, value in db.metadata.to_dict().items():
            assert value == self.metadata[key]

    def test_agr_blast_database_json(self):
        data = [
            agr_db.SequenceMetadata.from_dict(seq_md)
            for seq_md in self.sequence_metadata
        ]
        metadata = agr_db.Metadata.from_dict(self.metadata)
        db = agr_db.AgrBlastDatabases(data, metadata)
        db_as_str = json.dumps(db.to_dict())
        db_json = json.loads(db_as_str)
        assert db_json is not None
        assert len(db_json.get("data", [])) == len(self.sequence_metadata)
        assert db_json.get("metadata").get("contact") == self.metadata.get("contact")
