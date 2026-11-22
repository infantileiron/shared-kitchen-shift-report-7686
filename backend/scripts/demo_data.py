from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


ACCOUNTS = (
    ('manager@demo.local', '周岚', 'manager'),
    ('recorder@demo.local', '林秋', 'recorder'),
    ('observer@demo.local', '许闻', 'observer'),
)
STATIONS = (
    ('H01', '东侧烘焙灶', '东厨 · 烘焙区', 4),
    ('H02', '西侧炒制灶', '西厨 · 快炒区', 3),
    ('H03', '备餐试作灶', '备餐间 · 试作区', 2),
)
RULES = (
    ('H01', 'evening', '1.500', 2, 45, 8, 'kitchen'),
    ('H01', 'morning', '1.250', 3, 35, 6, 'kitchen'),
    ('H02', 'evening', '1.800', 2, 30, 5, 'operations'),
    ('H02', 'morning', '1.600', 2, 30, 5, 'operations'),
    ('H03', 'morning', '1.200', 2, 15, 10, 'operations'),
)


def windows():
    local = ZoneInfo('Asia/Shanghai')
    historical = datetime(2026, 11, 20, 17, tzinfo=local)
    live = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=55)
    return (
        ('HL-1120-E01', 'H01', 'evening', historical, 60,
         ((0, '0.600', 40), (1, '0.900', 30), (2, '1.200', 40), (3, '0.640', 40))),
        ('HL-1120-E02', 'H01', 'evening', historical + timedelta(hours=1), 30,
         ((0, '1.040', 40), (1, '0.850', 30))),
        ('HL-1120-E03', 'H01', 'evening', historical + timedelta(hours=2), 60,
         ((0, '0.900', 30), (2, '0.750', 30), (3, '1.050', 30))),
        ('HL-1120-W01', 'H02', 'evening', historical, 60, ((0, '0.000', 0),)),
        ('HL-WEST-NEXT', 'H02', 'morning', live, 175,
         ((0, '0.600', 30), (1, '0.900', 30), (2, '0.980', 30))),
    )
