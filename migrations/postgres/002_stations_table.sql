-- Stations registry metadata and relational constraints.
CREATE TABLE IF NOT EXISTS weather_stations (
    id text PRIMARY KEY,
    name text NOT NULL,
    brand text,
    latitude double precision,
    longitude double precision,
    created_at text,
    updated_at text,
    company_id text,
    company_code text,
    company_name text,
    company_image_url text,
    company_created_at text,
    company_updated_at text
);

CREATE INDEX IF NOT EXISTS idx_weather_stations_name ON weather_stations (name);
CREATE INDEX IF NOT EXISTS idx_weather_stations_company_code ON weather_stations (company_code);

-- Backfill missing station IDs from observation history before applying foreign keys
INSERT INTO weather_stations (id, name)
SELECT DISTINCT stnname, 'Station ' || stnname
FROM weather_raw
WHERE stnname NOT IN (SELECT id FROM weather_stations)
ON CONFLICT (id) DO NOTHING;

INSERT INTO weather_stations (id, name)
SELECT DISTINCT stnname, 'Station ' || stnname
FROM weather_daily
WHERE stnname NOT IN (SELECT id FROM weather_stations)
ON CONFLICT (id) DO NOTHING;

-- Foreign key constraints with idempotent DO block checks
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_weather_raw_station'
    ) THEN
        ALTER TABLE weather_raw
            ADD CONSTRAINT fk_weather_raw_station
            FOREIGN KEY (stnname) REFERENCES weather_stations(id)
            ON UPDATE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_weather_daily_station'
    ) THEN
        ALTER TABLE weather_daily
            ADD CONSTRAINT fk_weather_daily_station
            FOREIGN KEY (stnname) REFERENCES weather_stations(id)
            ON UPDATE CASCADE;
    END IF;
END $$;
