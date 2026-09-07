// In-memory history. Resets when the middleware restarts.
const MAX = 100;
const records = new Map();

export const store = {
  add(record) {
    records.set(record.id, record);
    if (records.size > MAX) records.delete(records.keys().next().value);
    return record;
  },
  get: (id) => records.get(id),
  list: () => [...records.values()].reverse(),
};
