#!/bin/bash

DATE=$(date +%F)
BACKUP_DIR="/root/backups"
DB_PATH="/root/BadhonStell/db.sqlite3"

mkdir -p $BACKUP_DIR

# Create backup
cp $DB_PATH $BACKUP_DIR/db_$DATE.sqlite3

# Upload to Dropbox
/root/Dropbox-Uploader/dropbox_uploader.sh upload $BACKUP_DIR/db_$DATE.sqlite3 /backups/

# Optional: delete local backup after upload
# rm -f $BACKUP_DIR/db_$DATE.sqlite3

