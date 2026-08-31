# Oshop Project Package
import pymysql
pymysql.install_as_MySQLdb()

# Compatibility patch for XAMPP MariaDB 10.4 with modern Django (5.1+/6.0+)
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

BaseDatabaseWrapper.check_database_version_supported = lambda self: None
DatabaseFeatures.can_return_columns_from_insert = False
DatabaseFeatures.can_return_rows_from_bulk_insert = False
