from datetime import datetime
from decimal import Decimal

from fastapi.encoders import jsonable_encoder


def payload(value):
    return jsonable_encoder(value, custom_encoder={Decimal: str, datetime: lambda stamp: stamp.isoformat()})
