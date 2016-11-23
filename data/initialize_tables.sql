-- Brendan King
-- 11/21/16

-- This file will be used to initialize the database backend stored in probannoweb.db

-- For storing session information and log-out times
CREATE TABLE IF NOT EXISTS Session(sid VARCHAR(60) PRIMARY KEY, logout INTEGER);

-- Storing Reaction Probabilities
CREATE TABLE IF NOT EXISTS Probanno(fasta_id VARCHAR(60) PRIMARY KEY, sid, probs BLOB,
  FOREIGN KEY (sid) REFERENCES Session(sid));

-- Storing Models
CREATE TABLE IF NOT EXISTS Model(sid VARCHAR(60), mid VARCHAR(60), model BLOB,
  PRIMARY KEY (sid, mid), FOREIGN KEY (sid) REFERENCES Session(sid));

-- Job Management
CREATE TABLE IF NOT EXISTS Jobs(jid INTEGER PRIMARY KEY AUTOINCREMENT, sid VARCHAR(60), job VARCHAR(40), target VARCHAR(60), status VARCHAR(60),
  FOREIGN KEY (sid) REFERENCES Session(sid));
