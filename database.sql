SQLALCHEMY_DATABASE_URI:  postgresql://postgres:postgres@localhost:5432/postgres
Current app config mode: Staging
Current app config mode: Staging
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 668e1eab419d

CREATE TABLE blacklist_tokens (
    id SERIAL NOT NULL, 
    token VARCHAR(500) NOT NULL, 
    blacklisted_on TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (token)
);

CREATE TABLE public_catalogs (
    id SERIAL NOT NULL, 
    name TEXT NOT NULL, 
    url TEXT NOT NULL, 
    description TEXT, 
    stac_version TEXT, 
    added_on TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (url)
);

CREATE TABLE stac_ingestion_status (
    id SERIAL NOT NULL, 
    time_started TIMESTAMP WITHOUT TIME ZONE, 
    time_finished TIMESTAMP WITHOUT TIME ZONE, 
    source_stac_api_url TEXT, 
    target_stac_api_url TEXT, 
    update BOOLEAN, 
    newly_stored_collections_count INTEGER, 
    newly_stored_collections TEXT, 
    updated_collections_count INTEGER, 
    updated_collections TEXT, 
    newly_stored_items_count INTEGER, 
    updated_items_count INTEGER, 
    already_stored_items_count INTEGER, 
    PRIMARY KEY (id)
);

CREATE TABLE "user" (
    id SERIAL NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    registered_on TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    admin BOOLEAN NOT NULL, 
    public_id VARCHAR(100), 
    username VARCHAR(50), 
    password_hash VARCHAR(100), 
    PRIMARY KEY (id), 
    UNIQUE (email), 
    UNIQUE (public_id), 
    UNIQUE (username)
);

CREATE TABLE stored_search_parameters (
    id SERIAL NOT NULL, 
    associated_catalog_id INTEGER NOT NULL, 
    bbox TEXT, 
    datetime TEXT, 
    collection TEXT, 
    used_search_parameters TEXT NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(associated_catalog_id) REFERENCES public_catalogs (id), 
    UNIQUE (used_search_parameters)
);

INSERT INTO alembic_version (version_num) VALUES ('668e1eab419d') RETURNING alembic_version.version_num;

COMMIT;

