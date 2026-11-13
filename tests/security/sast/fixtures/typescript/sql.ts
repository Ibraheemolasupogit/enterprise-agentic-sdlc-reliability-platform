// C5-M01 SQL construction controls. Synthetic; never executed.
type Db = {
  prepare(sql: string): { all(...v: unknown[]): unknown[] };
  exec(sql: string): void;
};
type Q = { query(sql: string, params?: object): Promise<unknown[]> };

const columns = "id, name, unit_price_minor";

export function unsafeTemplate(db: Db, search: string) {
  // ruleid: morrow.ts.sql-built-query
  return db.prepare(`SELECT ${columns} FROM products WHERE name = '${search}'`).all();
}

export function unsafeConcat(db: Db, category: string) {
  // ruleid: morrow.ts.sql-built-query
  return db.prepare("SELECT id FROM products WHERE category = '" + category + "'").all();
}

export function unsafeVariable(db: Db, order: string) {
  const sql = `SELECT id FROM products ORDER BY ${order}`;
  // ruleid: morrow.ts.sql-built-query
  return db.prepare(sql).all();
}

export async function unsafeQuery(q: Q, owner: string) {
  // ruleid: morrow.ts.sql-built-query
  return q.query(`DELETE FROM dbo.carts WHERE owner_key='${owner}'`);
}

export function unsafeExec(db: Db, table: string) {
  // ruleid: morrow.ts.sql-built-query
  db.exec("DELETE FROM " + table);
}

export function safeBound(db: Db, search: string, sort: string) {
  const where = "WHERE name LIKE ? ESCAPE '\\'";
  const order = sort === "price" ? "unit_price_minor" : "name";
  // ok: morrow.ts.sql-built-query
  return db.prepare(`SELECT ${columns} FROM products ${where} ORDER BY ${order}`).all(`%${search}%`);
}

export async function safeNamedParameters(q: Q, id: string, owner: string) {
  // ok: morrow.ts.sql-built-query
  return q.query("DELETE FROM dbo.carts WHERE id=@id AND owner_key=@owner", { id, owner });
}

function buildFilter(category: string) {
  return "WHERE category = '" + category + "'";
}

export function missedHelper(db: Db, category: string) {
  // todoruleid: morrow.ts.sql-built-query
  return db.prepare(buildFilter(category)).all();
}
