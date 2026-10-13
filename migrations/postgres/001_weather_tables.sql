-- Raw sensor text preserves historical error markers for the cleaning pipeline.
CREATE TABLE IF NOT EXISTS weather_raw (
    stnname text NOT NULL,
    utctime text NOT NULL,
    tempout text,
    humout text,
    windspd text,
    winddir text,
    bar text,
    solar text,
    rain15 text,
    created_at text,
    updated_at text,
    PRIMARY KEY (stnname, utctime)
);

CREATE TABLE IF NOT EXISTS weather_daily (
    stnname text NOT NULL,
    date date NOT NULL,
    temp_avg double precision,
    temp_min double precision,
    temp_max double precision,
    humidity_avg double precision,
    humidity_min double precision,
    humidity_max double precision,
    pressure_avg_hpa double precision,
    rainfall_total_mm double precision,
    solar_radiation_avg double precision,
    wind_speed_avg double precision,
    wind_speed_max double precision,
    wind_direction_deg double precision,
    wind_direction_name text,
    records_count bigint,
    PRIMARY KEY (stnname, date)
);
