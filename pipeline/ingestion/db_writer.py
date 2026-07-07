import psycopg2

def write_parcels_to_db(parcels):
    """
    Inserts normalized parcels into PostgreSQL.
    """
    conn = psycopg2.connect(
        dbname="housing",
        user="postgres",
        password="Deeznuff#1",
        host="localhost",
        port=5432
    )

    cur = conn.cursor()

    for p in parcels:
        cur.execute("""
            INSERT INTO parcels (
                parcel_id, county, address, city, state, zip,
                acreage, land_value, building_value, total_value, geometry
            ) VALUES (
                %(parcel_id)s, %(county)s, %(address)s, %(city)s, %(state)s, %(zip)s,
                %(acreage)s, %(land_value)s, %(building_value)s, %(total_value)s, %(geometry)s
            )
            ON CONFLICT (parcel_id) DO UPDATE SET
                county = EXCLUDED.county,
                address = EXCLUDED.address,
                city = EXCLUDED.city,
                zip = EXCLUDED.zip,
                acreage = EXCLUDED.acreage,
                land_value = EXCLUDED.land_value,
                building_value = EXCLUDED.building_value,
                total_value = EXCLUDED.total_value,
                geometry = EXCLUDED.geometry;
        """, p)

    conn.commit()
    cur.close()
    conn.close()

    return len(parcels)
