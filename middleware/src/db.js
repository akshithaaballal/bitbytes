import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_DIR = path.join(__dirname, '..', 'data');

if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const DB_PATH = process.env.DATABASE_PATH || path.join(DATA_DIR, 'bitbytes.db');
export const db = new DatabaseSync(DB_PATH);

// Enable WAL mode and foreign key constraints
db.exec(`
  PRAGMA journal_mode = WAL;
  PRAGMA foreign_keys = ON;

  CREATE TABLE IF NOT EXISTS readers (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    preferences TEXT NOT NULL DEFAULT '{}'
  );

  CREATE TABLE IF NOT EXISTS reader_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES readers(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL,
    family_id TEXT NOT NULL,
    is_revoked INTEGER NOT NULL DEFAULT 0,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS reader_progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES readers(id) ON DELETE CASCADE,
    post_id TEXT NOT NULL,
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    tz TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    created_at TEXT NOT NULL,
    UNIQUE(user_id, post_id, type)
  );

  CREATE TABLE IF NOT EXISTS login_attempts (
    key TEXT PRIMARY KEY,
    failed_count INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    last_attempt TEXT NOT NULL
  );

  CREATE INDEX IF NOT EXISTS idx_sessions_user ON reader_sessions(user_id);
  CREATE INDEX IF NOT EXISTS idx_sessions_family ON reader_sessions(family_id);
  CREATE INDEX IF NOT EXISTS idx_progress_user ON reader_progress(user_id);
`);
