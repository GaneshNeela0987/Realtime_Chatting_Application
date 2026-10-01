from database.database import engine,SessionLocal,Base
try:
    with engine.connect() as connection:
        print("Database connection successful!")

except Exception as e:
    print("Database connection failed:")
    print(e)