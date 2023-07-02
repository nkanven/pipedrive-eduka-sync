"""Import and Add new services in this loader"""

from services.database_backup import backup
from services.code_manager import load

load = {
    "database_backup": backup,
    "code_populate_db": load,
}
