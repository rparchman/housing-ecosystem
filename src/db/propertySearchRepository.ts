import { Pool } from 'pg';
import { PropertySearchQuery, PropertySearchResult } from '../models/propertySearch';

const pool = new Pool({
  // your connection config
});

function buildWhereClauses(query: PropertySearchQuery, params: any[]): string {
  const clauses: string[] = [];

  if (query.q) {
    params.push(`%${query.q}%`);
    clauses.push(`(LOWER(address) LIKE LOWER($${params.length}) OR LOWER(parcel_id) LIKE LOWER($${params.length}))`);
  }

  if (query.city) {
    params.push(query.city);
    clauses.push(`LOWER(city) = LOWER($${params.length})`);
  }

  if (query.county) {
    params.push(query.county);
    clauses.push(`LOWER(county) = LOWER($${params.length})`);
  }

  if (query.zip) {
    params.push(query.zip);
    clauses.push(`zip = $${params.length}`);
  }

  if (query.parcelId) {
    params.push(query.parcelId);
    clauses.push(`parcel_id = $${params.length}`);
  }

  if (query.status) {
    params.push(query.status);
    clauses.push(`status = $${params.length}`);
  }

  if (query.minPrice !== undefined) {
    params.push(query.minPrice);
    clauses.push(`price >= $${params.length}`);
  }

  if (query.maxPrice !== undefined) {
    params.push(query.maxPrice);
    clauses.push(`price <= $${params.length}`);
  }

  if (query.minSqft !== undefined) {
    params.push(query.minSqft);
    clauses.push(`sqft >= $${params.length}`);
  }

  if (query.maxSqft !== undefined) {
    params.push(query.maxSqft);
    clauses.push(`sqft <= $${params.length}`);
  }

  if (query.landBankOnly !== undefined) {
    params.push(query.landBankOnly);
    clauses.push(`land_bank = $${params.length}`);
  }

  if (query.hasStructure !== undefined) {
    params.push(query.hasStructure);
    clauses.push(`has_structure = $${params.length}`);
  }

  return clauses.length ? `WHERE ${clauses.join(' AND ')}` : '';
}

function buildOrderBy(sort?: string): string {
  switch (sort) {
    case 'price_asc':
      return 'ORDER BY price ASC NULLS LAST';
    case 'price_desc':
      return 'ORDER BY price DESC NULLS LAST';
    case 'date_added_desc':
      return 'ORDER BY created_at DESC';
    case 'sqft_desc':
      return 'ORDER BY sqft DESC NULLS LAST';
    default:
      return 'ORDER BY created_at DESC';
  }
}

export async function searchProperties(query: PropertySearchQuery): Promise<{
  results: PropertySearchResult[];
  total: number;
}> {
  const params: any[] = [];
  const where = buildWhereClauses(query, params);
  const orderBy = buildOrderBy(query.sort);

  const page = query.page || 1;
  const limit = query.limit || 25;
  const offset = (page - 1) * limit;

  const countSql = `SELECT COUNT(*)::int AS total FROM properties ${where};`;
  const countRes = await pool.query(countSql, params);
  const total = countRes.rows[0]?.total || 0;

  params.push(limit);
  params.push(offset);

  const dataSql = `
    SELECT
      id,
      parcel_id,
      address,
      city,
      county,
      zip,
      price,
      sqft,
      land_bank,
      status,
      lat,
      lng,
      updated_at
    FROM properties
    ${where}
    ${orderBy}
    LIMIT $${params.length - 1}
    OFFSET $${params.length};
  `;

  const dataRes = await pool.query(dataSql, params);

  const results: PropertySearchResult[] = dataRes.rows.map((row: any) => ({
    id: row.id,
    parcelId: row.parcel_id,
    address: row.address,
    city: row.city,
    county: row.county,
    zip: row.zip,
    price: row.price,
    sqft: row.sqft,
    landBank: row.land_bank,
    status: row.status,
    lat: row.lat,
    lng: row.lng,
    updatedAt: row.updated_at.toISOString?.() ?? row.updated_at,
  }));

  return { results, total };
}
