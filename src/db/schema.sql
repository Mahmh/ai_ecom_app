\c ai_ecom_db;

CREATE TABLE users(
    username         VARCHAR(255) NOT NULL PRIMARY KEY,
    password_hash    BYTEA NOT NULL,
    salt             BYTEA NOT NULL,
    bio              TEXT
);

CREATE TABLE products(
    product_id      SERIAL NOT NULL PRIMARY KEY,
    name            VARCHAR(511) NOT NULL,
    description     TEXT,
    image_file      VARCHAR(255),
    price           FLOAT,
    discount        FLOAT,
    category        VARCHAR(255),
    owner           VARCHAR(255) REFERENCES users(username)
);

CREATE TABLE interactions(
    username        VARCHAR(255) NOT NULL REFERENCES users(username),
    product_id      SERIAL NOT NULL REFERENCES products(product_id),
    rating          INT,
    reviews         TEXT[],  -- The same user can have multiple reviews on the same product
    sentiments      INT[],
    in_cart         BOOLEAN,
    PRIMARY KEY (username, product_id)  -- Composite key
)