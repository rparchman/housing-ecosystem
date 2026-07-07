import { PropertySearchQuery } from '../models/propertySearch';

export function parsePropertySearchQuery(raw: any): PropertySearchQuery {
  const page = raw.page ? Math.max(parseInt(raw.page, 10) || 1, 1) : 1;
  const limit = raw.limit ? Math.min(Math.max(parseInt(raw.limit, 10) || 25, 1), 100) : 25;

  return {
    q: raw.q?.toString().trim() || undefined,
    city: raw.city?.toString().trim() || undefined,
    county: raw.county?.toString().trim() || undefined,
    zip: raw.zip?.toString().trim() || undefined,
    parcelId: raw.parcel_id?.toString().trim() || undefined,
    status: raw.status?.toString().trim() || undefined,
    minPrice: raw.min_price ? Number(raw.min_price) : undefined,
    maxPrice: raw.max_price ? Number(raw.max_price) : undefined,
    minSqft: raw.min_sqft ? Number(raw.min_sqft) : undefined,
    maxSqft: raw.max_sqft ? Number(raw.max_sqft) : undefined,
    landBankOnly: raw.land_bank_only === 'true' ? true : raw.land_bank_only === 'false' ? false : undefined,
    hasStructure: raw.has_structure === 'true' ? true : raw.has_structure === 'false' ? false : undefined,
    sort: raw.sort?.toString().trim() || undefined,
    page,
    limit,
  };
}
