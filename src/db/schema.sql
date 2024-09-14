\c ai_ecom_db;

CREATE TABLE users(
    username     VARCHAR(255) NOT NULL PRIMARY KEY,
    password     VARCHAR(255) NOT NULL,
    bio          TEXT,
    cart         JSONB,
    ratings      JSONB
);

CREATE TABLE products(
    id           SERIAL NOT NULL PRIMARY KEY,
    name         VARCHAR(511) NOT NULL,
    description  TEXT,
    ratings      INT[],
    price        FLOAT,
    discount     FLOAT,
    category     VARCHAR(255),
    owner        VARCHAR(255) REFERENCES users(username),
    reviews      JSONB
);