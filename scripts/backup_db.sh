#!/usr/bin/env bash
# Clarere — günlük PostgreSQL yedeği (Neon).
#
# Kullanım:
#   chmod +x scripts/backup_db.sh
#   crontab -e → 30 3 * * * /opt/clarere/scripts/backup_db.sh >> /var/log/clarere-backup.log 2>&1
#
# Gerekli .env değişkenleri: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
# POSTGRES_USER, POSTGRES_PASSWORD
#
# Saklama: 14 gün. Neon free tier'da PITR sınırlı olduğu için bu yedek kritiktir.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
STAMP="$(date +%F_%H%M)"

# .env yükle (varsa)
if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ROOT_DIR/.env" | sed 's/\r$//')
  set +a
fi

: "${POSTGRES_HOST:?POSTGRES_HOST tanimli degil}"
: "${POSTGRES_DB:?POSTGRES_DB tanimli degil}"
: "${POSTGRES_USER:?POSTGRES_USER tanimli degil}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD tanimli degil}"

mkdir -p "$BACKUP_DIR"
TARGET="$BACKUP_DIR/clarere-${STAMP}.sql.gz"

echo "[$(date -Is)] Yedek aliniyor -> $TARGET"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  --host="$POSTGRES_HOST" \
  --port="${POSTGRES_PORT:-5432}" \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  --no-owner --no-privileges \
  | gzip > "$TARGET"

echo "[$(date -Is)] Yedek tamam: $(du -h "$TARGET" | cut -f1)"

# Eski yedekleri temizle
find "$BACKUP_DIR" -name 'clarere-*.sql.gz' -mtime "+$RETENTION_DAYS" -delete
echo "[$(date -Is)] ${RETENTION_DAYS} günden eski yedekler silindi."
