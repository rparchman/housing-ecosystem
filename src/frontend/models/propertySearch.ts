export interface PropertySearchQuery {
  q?: string;
  city?: string;
  county?: string;
  zip?: string;
  parcelId?: string;
  status?: string;
  minPrice?: number;
  maxPrice?: number;
  minSqft?: number;
  maxSqft?: number;
  landBankOnly?: boolean;
  hasStructure?: boolean;
  sort?: string;
  page?: number;
  limit?: number;
}

export interface PropertySearchResult {
  id: string;
  parcelId: string;
  address: string;
  city: string;
  county: string;
  zip: string;
  price: number | null;
  sqft: number | null;
  landBank: boolean;
  status: string;
  lat: number | null;
  lng: number | null;
  updatedAt: string;
}
