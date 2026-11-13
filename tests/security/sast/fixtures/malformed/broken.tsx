// C5-M07 malformed TSX: must be a parse failure, never clean.
export function Broken() {
  return <div><span>unclosed</div>;
}
