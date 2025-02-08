import os
import shutil
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bluesky-event-sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BACKUP_DIR = 'database/backups'
DATABASE_FILE = 'database/events.db'
MAX_BACKUPS = 5

def create_backup():
    logger.info("Starting database backup process")
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logger.info(f"Created backup directory: {BACKUP_DIR}")
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'events_{timestamp}.db')
    
    try:
        shutil.copy2(DATABASE_FILE, backup_file)
        logger.info(f"Backup created: {backup_file}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise

def cleanup_old_backups():
    logger.info("Starting cleanup of old backups")
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith('events_')],
        key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x))
    )
    
    while len(backups) > MAX_BACKUPS:
        old_backup = backups.pop(0)
        old_backup_path = os.path.join(BACKUP_DIR, old_backup)
        try:
            os.remove(old_backup_path)
            logger.info(f"Deleted old backup: {old_backup_path}")
        except Exception as e:
            logger.error(f"Failed to delete old backup: {e}")

if __name__ == "__main__":
    logger.info("Backup script started")
    create_backup()
    cleanup_old_backups()
    logger.info("Backup script completed")