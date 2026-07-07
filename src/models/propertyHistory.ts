export interface PropertyHistoryEvent {
  id: string;
  propertyId: string;
  eventType: string; // 'status_change' | 'price_change' | 'ownership_change' | 'note'
  oldValue: string | null;
  newValue: string | null;
  createdAt: string;
  source: string; // 'county', 'manual', 'pipeline'
}
