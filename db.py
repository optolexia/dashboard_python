#import dotenv
from sqlalchemy import create_engine
from connection_utils import ConnectionParameters

# Load environment variables from .env
#dotenv.load_dotenv()

# Read connection parameters
cp = ConnectionParameters()

# ─────────────────────────────────────────────
# PostgreSQL engine
# ─────────────────────────────────────────────

pg_engine = create_engine(
    f"postgresql+psycopg2://{cp.pg_user}:{cp.pg_pass}@{cp.pg_host}:5432/{cp.pg_db}",
    connect_args={"sslmode": "require"},
    pool_pre_ping=True,   # Avoid stale connections
    pool_size=5,
    max_overflow=10
)

# ─────────────────────────────────────────────
# MySQL engine
# ─────────────────────────────────────────────

mysql_engine = create_engine(
    f"mysql+mysqlconnector://{cp.mysql_user}:{cp.mysql_pass}@{cp.mysql_host}:3306/{cp.mysql_db}",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)
