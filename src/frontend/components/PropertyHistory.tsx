import { useEffect, useState } from 'react';
import { getPropertyHistory } from '../api/propertyHistoryApi';
import { PropertyHistoryEvent } from '../models/propertyHistory';

interface Props {
  propertyId: string;
}

export function PropertyHistory({ propertyId }: Props) {
  const [events, setEvents] = useState<PropertyHistoryEvent[]>([]);

  useEffect(() => {
    if (!propertyId) return;

    getPropertyHistory(propertyId).then(setEvents);
  }, [propertyId]);

  if (!events.length) {
    return <div>No history available.</div>;
  }

  return (
    <div style={{ marginTop: '20px' }}>
      <h3>History</h3>
      {events.map((e) => (
        <div key={e.id} style={{ borderBottom: '1px solid #ddd', padding: '8px 0' }}>
          <div>{new Date(e.createdAt).toLocaleString()}</div>
          <div>Type: {e.eventType}</div>
          <div>From: {e.oldValue ?? 'N/A'} → To: {e.newValue ?? 'N/A'}</div>
          <div>Source: {e.source}</div>
        </div>
      ))}
    </div>
  );
}
