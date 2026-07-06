#!/bin/bash
# Database backup script for email-system
# Usage: ./scripts/backup.sh [output-dir]

set -euo pipefail

BACKUP_DIR="${1:-./data/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="email_system"
DB_USER="${MYSQL_USER:-email_user}"
DB_PASS="${MYSQL_PASSWORD:-email_password}"
DB_HOST="${MYSQL_HOST:-localhost}"

mkdir -p "$BACKUP_DIR"

echo "=== Backing up $DB_NAME to $BACKUP_DIR ==="

# Dump schema and data
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" \
  --single-transaction --routines --triggers --events \
  "$DB_NAME" | gzip > "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Keep only last 30 days
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +30 -delete

echo "=== Backup complete: ${DB_NAME}_${TIMESTAMP}.sql.gz ==="
echo "Size: $(ls -lh "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz" | awk '{print $5}')"
