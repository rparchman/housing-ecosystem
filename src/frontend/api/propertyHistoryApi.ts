import { PropertyHistoryEvent } from '../models/propertyHistory';

const BASE_URL = 'http://localhost:3000';

export async function getPropertyHistory(propertyId: string): Promise<PropertyHistoryEvent[]> {
  const res = await fetch(`${BASE_URL}/properties/${propertyId}/history`);

  if (!res.ok) {
    throw new Error(`Failed to load property history: ${res.status}`);
  }

  return await res.json();
}
