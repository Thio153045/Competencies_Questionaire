-- Skema database Kuesioner Kompetensi
-- Jalankan: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS kuesioner_kompetensi
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE kuesioner_kompetensi;

CREATE TABLE IF NOT EXISTS admin (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(50)  NOT NULL UNIQUE,
  password_hash VARCHAR(100) NOT NULL,
  nama          VARCHAR(100) NOT NULL,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS responden (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  nama              VARCHAR(150) NOT NULL,
  posisi            VARCHAR(150) NOT NULL,
  unit_kerja        VARCHAR(150) NOT NULL,
  lama_bekerja      DECIMAL(4,1) NOT NULL,
  tanggal_pengisian DATE NOT NULL,
  pernyataan        TINYINT(1) NOT NULL DEFAULT 0,
  created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS jawaban (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  responden_id    INT NOT NULL,
  kode_kompetensi CHAR(1) NOT NULL,
  jawaban         TEXT NOT NULL,
  UNIQUE KEY uq_jawaban (responden_id, kode_kompetensi),
  CONSTRAINT fk_jawaban_responden FOREIGN KEY (responden_id)
    REFERENCES responden(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS penilaian (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  jawaban_id INT NOT NULL UNIQUE,
  skor       TINYINT NOT NULL,
  alasan     TEXT,
  sumber     ENUM('AI', 'Aturan') NOT NULL,
  model      VARCHAR(100) NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT chk_skor CHECK (skor BETWEEN 1 AND 5),
  CONSTRAINT fk_penilaian_jawaban FOREIGN KEY (jawaban_id)
    REFERENCES jawaban(id) ON DELETE CASCADE
) ENGINE=InnoDB;
