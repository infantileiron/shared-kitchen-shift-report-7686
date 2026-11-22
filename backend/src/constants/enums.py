from enum import StrEnum


class Role(StrEnum):
    MANAGER = 'manager'
    RECORDER = 'recorder'
    OBSERVER = 'observer'


class ShiftKind(StrEnum):
    MORNING = 'morning'
    EVENING = 'evening'


class Mailbox(StrEnum):
    KITCHEN = 'kitchen'
    OPERATIONS = 'operations'


class Outcome(StrEnum):
    ALERTED = 'alerted'
    COOLDOWN = 'cooldown'
    WITHIN_RULE = 'within_rule'
    UNMEASURABLE = 'unmeasurable'


class Reason(StrEnum):
    READINGS_BACKFILLED = 'readings_backfilled'
    COOLDOWN_BOUNDARY = 'cooldown_boundary'


SLOT_MINUTES = 15
