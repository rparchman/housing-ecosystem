import { PropertyDetail } from '../models/propertyDetail';

const BASE_URL = 'http://localhost:3000';

export async function getPropertyDetail(id: string): Promise<PropertyDetail> {
  const res = await fetch(`${BASE_URL}/properties/${id}`);

  if (!res.ok) {
    throw new Error(`Failed to load property detail: ${res.status}`);
  }

  return await res.json();
}
