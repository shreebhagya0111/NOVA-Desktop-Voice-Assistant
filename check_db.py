import inspect
import app.database

print("\n========== MODULE CHECK ==========")

print("Loaded database file:")
print(app.database.__file__)

print("\nActual init_db function:")
print(inspect.getsource(app.database.init_db))

print("\n========== RUNNING INIT_DB ==========")

app.database.init_db()

connection = app.database.get_db_connection()

tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("\nTables found after initialization:")

for table in tables:
    print(table["name"])

connection.close()

print("\n========== CHECK COMPLETED ==========")