CREATE TABLE countries (
    country_code INTEGER PRIMARY KEY,
    country_name TEXT NOT NULL,
    iso_code CHAR(3) UNIQUE
);