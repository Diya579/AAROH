from backend.database import engine, Base
import backend.models as models


print("Creating AAROH database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")