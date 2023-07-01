"""Import and Add new services in this loader"""

from services.database_backup import backup

load = {
    "database_backup": backup,
}
