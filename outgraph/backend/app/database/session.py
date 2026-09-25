"""Database Session & Initialization."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from ..core.config import settings

# SQLite configuration with multi-thread check disabled
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Dependency for database session."""
    init_db()
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def init_db():
    """Initializes tables in database and applies lightweight SQLite column migrations if needed."""
    Base.metadata.create_all(bind=engine)

    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                from sqlalchemy import inspect, text
                inspector = inspect(engine)
                table_names = set(inspector.get_table_names())

                if "observations" in table_names:
                    existing_cols = {c["name"] for c in inspector.get_columns("observations")}
                    new_cols = [
                        ("product_id", "TEXT"),
                        ("mission", "TEXT"),
                        ("instrument", "TEXT"),
                        ("product_type", "TEXT"),
                        ("processing_level", "TEXT"),
                        ("num_bands", "REAL DEFAULT 1.0"),
                        ("data_type", "TEXT DEFAULT 'uint8'"),
                        ("nodata_value", "REAL"),
                        ("provenance_json", "TEXT DEFAULT '{}'"),
                        ("metadata_source_json", "TEXT DEFAULT '{}'"),
                        ("is_synthetic", "BOOLEAN DEFAULT 1"),
                    ]
                    for col_name, col_type in new_cols:
                        if col_name not in existing_cols:
                            conn.execute(text(f"ALTER TABLE observations ADD COLUMN {col_name} {col_type}"))

                # Ensure is_synthetic exists on other tables
                for tbl in ["correspondences", "correspondence_evidence", "lunar_entities", "knowledge_gaps", "recommendations"]:
                    if tbl in table_names:
                        existing_cols = {c["name"] for c in inspector.get_columns(tbl)}
                        if "is_synthetic" not in existing_cols:
                            conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN is_synthetic BOOLEAN DEFAULT 1"))

                conn.commit()
        except Exception:
            pass

