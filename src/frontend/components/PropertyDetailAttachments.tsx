interface Props {
  attachments: Array<{
    id: string;
    url: string;
    name: string;
    type: string;
  }>;
}

export function PropertyDetailAttachments({ attachments }: Props) {
  if (!attachments.length) {
    return <div>No attachments available.</div>;
  }

  return (
    <div style={{ marginTop: '20px' }}>
      <h3>Attachments</h3>

      {attachments.map((a) => (
        <div key={a.id} style={{ marginBottom: '8px' }}>
          <a href={a.url} target="_blank" rel="noopener noreferrer">
            {a.name} ({a.type})
          </a>
        </div>
      ))}
    </div>
  );
}
