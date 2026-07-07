interface Props {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onPageChange }: Props) {
  if (totalPages <= 1) return null;

  function goTo(p: number) {
    if (p < 1 || p > totalPages) return;
    onPageChange(p);
  }

  return (
    <div style={{ marginTop: '20px', display: 'flex', gap: '8px' }}>
      <button onClick={() => goTo(page - 1)} disabled={page === 1}>
        Prev
      </button>

      <span>Page {page} of {totalPages}</span>

      <button onClick={() => goTo(page + 1)} disabled={page === totalPages}>
        Next
      </button>
    </div>
  );
}
