/*
 * channel.sql
 * fastapi_kafka
 *
 * Created by Xavier Cañadas on 15/4/2025
 * Copyright (c) 2025. All rights reserved.
 */

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

-- Add a channel to the table
INSERT INTO channels (channel_name, description)
VALUES ('Swifties', 'The best fan base');

-- Add users to a channel
INSERT INTO user_channels (username, channel_id)
VALUES ('taylor.swift', 1),
       ('olivia.rodrigo', 1)
