INSERT OR IGNORE INTO categories(name,slug) VALUES
('Arcade','arcade'),('Puzzle','puzzle'),('Strategy','strategy'),('Action','action');
INSERT OR IGNORE INTO users(username,email,password_hash,display_name,role,created_at)
VALUES
('student','student@example.test','$argon2id$v=19$m=65536,t=3,p=2$o9aWbEzDW3v8f/8cfBG7WQ$cveliXvQwSxGopkv6BVyyOdFeqcLil/9UHxkNHj7srA','Student Player','user','2026-11-24T00:00:00+00:00'),
('admin','admin@example.test','$argon2id$v=19$m=65536,t=3,p=2$n+eA7ByEUb0Ck8vbsgaSsQ$KE2iSImb76sb6eK/DEjr59e6aW+6sMW+aE7vck42NnU','Lab Administrator','admin','2026-11-24T00:00:00+00:00');
INSERT OR IGNORE INTO games(slug,title,category_id,description,difficulty,file_path,rating,accent,artwork_slug,created_at)
SELECT 'orbital-drift','Orbital Drift',id,'Pilot a tiny research craft through a calm field of drifting asteroids. A short original browser game made for this training lab.','Easy','app/static/downloads/orbital-drift.zip','★ 4.8','#46d6c5','orbital-drift','2026-11-24T00:00:00+00:00' FROM categories WHERE slug='arcade';
INSERT OR IGNORE INTO games(slug,title,category_id,description,difficulty,file_path,rating,accent,artwork_slug,created_at)
SELECT 'signal-garden','Signal Garden',id,'Route a signal through a small grid of mirrors and relays.','Relaxed','app/static/downloads/signal-garden.zip','★ 4.6','#b6a0ff','signal-garden','2026-11-24T00:00:00+00:00' FROM categories WHERE slug='puzzle';
INSERT OR IGNORE INTO games(slug,title,category_id,description,difficulty,file_path,rating,accent,artwork_slug,created_at)
SELECT 'tiny-kingdoms','Tiny Kingdoms',id,'Arrange friendly outposts and keep their supply lines connected.','Thoughtful','app/static/downloads/tiny-kingdoms.zip','★ 4.7','#f0bd6b','tiny-kingdoms','2026-11-24T00:00:00+00:00' FROM categories WHERE slug='strategy';
INSERT OR IGNORE INTO games(slug,title,category_id,description,difficulty,file_path,rating,accent,artwork_slug,created_at)
SELECT 'pixel-sprint','Pixel Sprint',id,'A compact keyboard-first obstacle course with original shapes.','Fast','app/static/downloads/pixel-sprint.zip','★ 4.5','#ff8a80','pixel-sprint','2026-11-24T00:00:00+00:00' FROM categories WHERE slug='action';
