-- Reference schema (MySQL 8). Django migrations are the source of truth; this mirrors them for review.
CREATE TABLE users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  password VARCHAR(128) NOT NULL,              -- PBKDF2-SHA256 hash, never plain text
  last_login DATETIME(6) NULL,
  is_superuser TINYINT(1) NOT NULL,
  username VARCHAR(150) NOT NULL UNIQUE,
  first_name VARCHAR(150) NOT NULL,
  last_name VARCHAR(150) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  is_staff TINYINT(1) NOT NULL,
  is_active TINYINT(1) NOT NULL,
  date_joined DATETIME(6) NOT NULL
);

CREATE TABLE cards (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  card_holder_name VARCHAR(100) NOT NULL,
  card_type VARCHAR(6) NOT NULL,               -- CREDIT | DEBIT
  brand VARCHAR(12) NOT NULL,
  masked_number VARCHAR(25) NOT NULL,          -- **** **** **** 1111
  last4 CHAR(4) NOT NULL,
  expiry_month SMALLINT UNSIGNED NOT NULL,
  expiry_year SMALLINT UNSIGNED NOT NULL,
  created_at DATETIME(6) NOT NULL,
  -- NOTE: no full card number column, no CVV column
  CONSTRAINT fk_cards_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_cards_user_last4 (user_id, last4)
);

CREATE TABLE transactions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  reference CHAR(36) NOT NULL UNIQUE,
  user_id BIGINT NOT NULL,
  card_id BIGINT NULL,
  amount DECIMAL(12,2) NOT NULL,
  currency CHAR(3) NOT NULL,
  description VARCHAR(255) NOT NULL,
  status VARCHAR(7) NOT NULL,                  -- PENDING | SUCCESS | FAILED
  failure_reason VARCHAR(255) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT fk_txn_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_txn_card FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE SET NULL,
  INDEX idx_txn_status (status),
  INDEX idx_txn_created (created_at)
);

CREATE TABLE admin_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  admin_id BIGINT NULL,
  action VARCHAR(20) NOT NULL,
  details LONGTEXT NOT NULL,
  created_at DATETIME(6) NOT NULL,
  CONSTRAINT fk_log_admin FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
);
