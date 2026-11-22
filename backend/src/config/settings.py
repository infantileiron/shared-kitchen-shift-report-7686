import os

DB = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'dbname': os.getenv('DB_NAME', 'hobs'),
    'user': os.getenv('DB_USER', 'hobs'),
    'password': os.getenv('DB_PASSWORD', 'hobs-dev'),
    'connect_timeout': 3,
    'options': '-c timezone=UTC -c statement_timeout=6000',
}
JWT_SECRET = os.getenv('JWT_SECRET', 'hob-dispatch-development-only-change-me')
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
WORKER_METRICS = 'hob-dispatch:scheduler'
