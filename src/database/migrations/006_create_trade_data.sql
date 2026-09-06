CREATE TABLE trade_data (
    trade_data_id BIGSERIAL PRIMARY KEY,

    source_object_id BIGINT NOT NULL
        REFERENCES source_objects(source_object_id),

    ingestion_run_id BIGINT NOT NULL
        REFERENCES ingestion_runs(ingestion_run_id),

    year INTEGER NOT NULL,

    reporter_code INTEGER NOT NULL
        REFERENCES countries(country_code),

    flow_code CHAR(1) NOT NULL
        CHECK (flow_code IN ('M', 'X')),

    partner_code INTEGER NOT NULL
        REFERENCES countries(country_code),

    commodity_code TEXT NOT NULL
        REFERENCES commodities(commodity_code),

    mot_code INTEGER NOT NULL
        REFERENCES transport_modes(mot_code),

    qty NUMERIC,

    primary_value NUMERIC,

    is_reported BOOLEAN NOT NULL DEFAULT TRUE,

    is_aggregate BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE (
        year,
        reporter_code,
        flow_code,
        partner_code,
        commodity_code,
        mot_code
    )
);