-- LifeOS Telegram Self-Bot Schema
-- Tables: saved_items, bio_state, bot_logs

CREATE TABLE IF NOT EXISTS saved_items (
    id              SERIAL PRIMARY KEY,
    save_code       TEXT UNIQUE NOT NULL,
    save_type       TEXT NOT NULL CHECK (save_type IN ('forward', 'deep')),
    origin_chat_id  BIGINT,
    origin_msg_id   BIGINT,
    saved_chat_id   BIGINT,
    saved_msg_id    BIGINT,
    sender_name     TEXT,
    sender_id       BIGINT,
    mime_type       TEXT,
    file_id         TEXT,
    file_size       BIGINT,
    media_type      TEXT,
    tags            TEXT[] DEFAULT '{}',
    caption         TEXT,
    owner_id        BIGINT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE saved_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_saved_items" ON saved_items;
CREATE POLICY "anon_select_saved_items" ON saved_items FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_saved_items" ON saved_items;
CREATE POLICY "anon_insert_saved_items" ON saved_items FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_saved_items" ON saved_items;
CREATE POLICY "anon_update_saved_items" ON saved_items FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_saved_items" ON saved_items;
CREATE POLICY "anon_delete_saved_items" ON saved_items FOR DELETE
    TO anon, authenticated USING (true);

CREATE INDEX IF NOT EXISTS idx_saved_items_owner ON saved_items (owner_id);
CREATE INDEX IF NOT EXISTS idx_saved_items_created ON saved_items (created_at DESC);

CREATE TABLE IF NOT EXISTS bio_state (
    id           SERIAL PRIMARY KEY,
    owner_id     BIGINT UNIQUE NOT NULL,
    template     TEXT NOT NULL DEFAULT '🕒 {time} | 💭 {mood}',
    mood         TEXT NOT NULL DEFAULT '😊',
    custom_text  TEXT NOT NULL DEFAULT '',
    is_active    BOOLEAN NOT NULL DEFAULT FALSE,
    last_bio     TEXT NOT NULL DEFAULT '',
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE bio_state ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_bio_state" ON bio_state;
CREATE POLICY "anon_select_bio_state" ON bio_state FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_bio_state" ON bio_state;
CREATE POLICY "anon_insert_bio_state" ON bio_state FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_bio_state" ON bio_state;
CREATE POLICY "anon_update_bio_state" ON bio_state FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_bio_state" ON bio_state;
CREATE POLICY "anon_delete_bio_state" ON bio_state FOR DELETE
    TO anon, authenticated USING (true);

CREATE TABLE IF NOT EXISTS bot_logs (
    id         SERIAL PRIMARY KEY,
    owner_id   BIGINT NOT NULL,
    level      TEXT NOT NULL CHECK (level IN ('INFO', 'WARN', 'ERROR')),
    message    TEXT NOT NULL,
    context    JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE bot_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_bot_logs" ON bot_logs;
CREATE POLICY "anon_select_bot_logs" ON bot_logs FOR SELECT
    TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_insert_bot_logs" ON bot_logs;
CREATE POLICY "anon_insert_bot_logs" ON bot_logs FOR INSERT
    TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_update_bot_logs" ON bot_logs;
CREATE POLICY "anon_update_bot_logs" ON bot_logs FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "anon_delete_bot_logs" ON bot_logs;
CREATE POLICY "anon_delete_bot_logs" ON bot_logs FOR DELETE
    TO anon, authenticated USING (true);

CREATE INDEX IF NOT EXISTS idx_bot_logs_owner ON bot_logs (owner_id);
CREATE INDEX IF NOT EXISTS idx_bot_logs_created ON bot_logs (created_at DESC);
