#!/bin/bash

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_FILE="backend/mfa_auth.db"

mkdir -p $BACKUP_DIR

if [ -f "$DB_FILE" ]; then
    cp $DB_FILE "$BACKUP_DIR/mfa_auth_$TIMESTAMP.db"
    echo "✅ Database backed up to $BACKUP_DIR/mfa_auth_$TIMESTAMP.db"
else
    echo "❌ Database file not found!"
fi
