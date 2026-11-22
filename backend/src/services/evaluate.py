from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from src.constants.enums import Outcome, SLOT_MINUTES


def normalized(gas, minutes):
    if not minutes:
        return None
    return (gas * 60 / minutes).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


def evaluate(shift, entries, previous_due):
    readings = {entry['sampled_at']: entry for entry in entries}
    step = timedelta(minutes=SLOT_MINUTES)
    sample_at = shift['starts_at']
    gas = Decimal(0)
    burner_minutes = streak = longest = valid = missing = idle = overruns = 0
    slots = []
    while sample_at < shift['ends_at']:
        entry = readings.get(sample_at)
        state, intensity = 'missing', None
        if entry is None:
            missing += 1
        elif not entry['burner_minutes']:
            state = 'idle'
            idle += 1
        else:
            valid += 1
            minutes = entry['burner_minutes']
            gas += entry['gas_m3']
            burner_minutes += minutes
            intensity = normalized(entry['gas_m3'], minutes)
            # Use exact bounds before display rounding.
            state = 'over' if entry['gas_m3'] * 60 > shift['threshold'] * minutes else 'within'
        if state == 'over':
            overruns += 1
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0
        slots.append({'sampled_at': sample_at, 'state': state, 'intensity': intensity, 'streak': streak,
                      'gas_m3': entry['gas_m3'] if entry else None,
                      'burner_minutes': entry['burner_minutes'] if entry else None})
        sample_at += step
    cooldown_until = previous_due + timedelta(minutes=shift['cooldown_minutes']) if previous_due else None
    outcome = Outcome.UNMEASURABLE if not valid else Outcome.WITHIN_RULE
    if longest >= shift['consecutive']:
        outcome = Outcome.COOLDOWN if cooldown_until and shift['due_at'] < cooldown_until else Outcome.ALERTED
    return {'shift_code': shift['code'], 'station_code': shift['station_code'],
            'starts_at': shift['starts_at'], 'ends_at': shift['ends_at'], 'due_at': shift['due_at'],
            'rule': {key: shift[key] for key in ('rule_version', 'threshold', 'consecutive', 'cooldown_minutes', 'delay_minutes', 'mailbox')},
            'gas_m3': gas, 'burner_minutes': burner_minutes, 'intensity': normalized(gas, burner_minutes),
            'valid_slots': valid, 'missing_slots': missing, 'idle_slots': idle, 'over_slots': overruns,
            'longest_streak': longest, 'previous_alert_due': previous_due, 'cooldown_until': cooldown_until,
            'outcome': outcome, 'slots': slots}
