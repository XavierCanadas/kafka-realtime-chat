/*
 * init_database.sql
 * fastapi_kafka
 *
 * Created by Xavier Cañadas on 15/4/2025
 * Copyright (c) 2025. All rights reserved.
 */

-- Create the user table
CREATE TABLE IF NOT EXISTS users
(
    username      VARCHAR(50) UNIQUE  NOT NULL PRIMARY KEY,
    first_name    VARCHAR(50)         NOT NULL,
    last_name     VARCHAR(50)         NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    disabled      BOOLEAN DEFAULT FALSE
);

-- create the channel table
CREATE TABLE IF NOT EXISTS channels
(
    id           SERIAL PRIMARY KEY,
    channel_name VARCHAR(50) UNIQUE NOT NULL,
    description  VARCHAR(255),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- relation with the user table, relation many to many
CREATE TABLE IF NOT EXISTS user_channels
(
    username   VARCHAR(50) NOT NULL,
    channel_id INTEGER     NOT NULL,
    PRIMARY KEY (username, channel_id),
    FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
);

-- Add a user to the table
INSERT INTO users (username, first_name, last_name, email, password_hash)
VALUES ('olivia.rodrigo',
        'Olivia',
        'Rodrigo',
        'olivia.rodrigo@exemple.com',
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW' -- password: 'secret'
       ),
       ('taylor.swift',
        'Taylor',
        'Swift',
        'taylor.swift@exemple.com',
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW' -- password: 'secret'
       ),
       ('gracie.abrams',
        'Gracie',
        'Abrams',
        'gracie.abrams@exemple.com',
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW' -- password: 'secret'
       )
ON CONFLICT (username) DO NOTHING;

-- Add a channel to the table
INSERT INTO channels (channel_name, description)
VALUES ('Swifties', 'The best fan base')
ON CONFLICT (channel_name) DO NOTHING;

-- Add users to a channel
INSERT INTO user_channels (username, channel_id)
VALUES ('taylor.swift', 1),
       ('olivia.rodrigo', 1),
       ('gracie.abrams', 1)
ON CONFLICT (username, channel_id) DO NOTHING;