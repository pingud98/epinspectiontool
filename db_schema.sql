CREATE TABLE inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inspector_name TEXT NOT NULL,
    location TEXT NOT NULL,
    inspection_date TEXT NOT NULL,
    installation_name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

INSERT INTO checklist_items (name) VALUES
('Check electrical wiring'),
('Check plumbing'),
('Check fire safety'),
('Check electrical safety'),
('Check water pressure'),
('Check drainage'),
('Check structural integrity'),
('Check emergency exits'),
('Check fire extinguishers'),
('Check ventilation');

CREATE TABLE inspection_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id INTEGER NOT NULL,
    photo_path TEXT NOT NULL,
    comment TEXT,
    resolved INTEGER DEFAULT 0,
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inspection_id) REFERENCES inspections(id)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    logo_path TEXT
);