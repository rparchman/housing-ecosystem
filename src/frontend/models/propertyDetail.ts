export interface PropertyDetail {
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

  // County-specific fields
  assessedValue?: number | null;
  taxableValue?: number | null;
  yearBuilt?: number | null;
  lotSize?: number | null;

  // Attachments
  attachments: Array<{
    id: string;
    url: string;
    name: string;
    type: string;
  }>;
}
