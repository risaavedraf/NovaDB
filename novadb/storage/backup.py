import os
import glob
import shutil
import argparse
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)

def backup_db(db_path: str, backup_dir: str, rotate: int) -> None:
    """
    Genera una copia rotativa del archivo de base de datos de NovaDB.
    Mantiene siempre los últimos N backups, eliminando los más antiguos.
    """
    if not os.path.exists(db_path):
        logger.warning("No database found at %s for backup", db_path)
        return
        
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext: str = ".msgpack" if ".msgpack" in db_path else ".json"
    backup_file: str = os.path.join(backup_dir, f"nova_backup_{timestamp}{ext}")
    
    # 1. Copiar archivo (Backup instantáneo O(1) vía OS)
    shutil.copy2(db_path, backup_file)
    logger.info("Backup created: %s", backup_file)
    
    if rotate > 0:
        backups: List[str] = sorted(glob.glob(os.path.join(backup_dir, f"nova_backup_*{ext}")), reverse=True)
        if len(backups) > rotate:
            for old_backup in backups[rotate:]:
                os.remove(old_backup)
                logger.debug("Old backup rotated (deleted): %s", old_backup)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup automatizado para NovaDB con rotación")
    parser.add_argument("--db-path", type=str, default="./db/nova.msgpack", help="Ruta de la DB activa")
    parser.add_argument("--backup-dir", type=str, default="./db/backups", help="Directorio destino")
    parser.add_argument("--rotate", type=int, default=7, help="Cantidad de backups a mantener")
    args = parser.parse_args()
    
    backup_db(args.db_path, args.backup_dir, args.rotate)
