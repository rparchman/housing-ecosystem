export interface PropertyHistoryEvent {
  id: string;
  propertyId: string;
  eventType: string;
  oldValue: string | null;
  newValue: string | null;
  createdAt: string;
  source: string;
}
