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
       );


