import sqlalchemy
import databases
from shortenerapi.core.config import get_settings

settings = get_settings()

metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(
    settings.DATABASE_URL, connect_args={'check_same_thread':False}
)
database = databases.Database(
    settings.DATABASE_URL
)

url_table = sqlalchemy.Table(
    'urls',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('original_url', sqlalchemy.String, nullable=False),
    sqlalchemy.Column('expires_at', sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column('short_code', sqlalchemy.String, unique=True, nullable=False),
    sqlalchemy.Column('click_count', sqlalchemy.Integer, default=0, nullable=False),
    sqlalchemy.Column('is_active', sqlalchemy.Boolean, default=True, nullable=False)
)

metadata.create_all(engine)