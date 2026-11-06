CREATE DATABASE IF NOT EXISTS sentinel_guard
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sentinel_guard;

CREATE TABLE IF NOT EXISTS analyses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  comment_text TEXT NOT NULL,
  clean_text TEXT NOT NULL,
  is_toxic TINYINT(1) NOT NULL DEFAULT 0,
  moderation_result VARCHAR(32) NOT NULL,
  toxic FLOAT NOT NULL DEFAULT 0,
  severe_toxic FLOAT NOT NULL DEFAULT 0,
  obscene FLOAT NOT NULL DEFAULT 0,
  threat FLOAT NOT NULL DEFAULT 0,
  insult FLOAT NOT NULL DEFAULT 0,
  identity_hate FLOAT NOT NULL DEFAULT 0,
  max_confidence FLOAT NOT NULL DEFAULT 0,
  triggered_labels JSON NULL,
  source VARCHAR(64) DEFAULT 'web',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_created_at (created_at),
  INDEX idx_is_toxic (is_toxic),
  INDEX idx_moderation (moderation_result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS model_runs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  model_name VARCHAR(64) NOT NULL,
  metrics_json JSON NOT NULL,
  trained_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
