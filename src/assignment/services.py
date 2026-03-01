from datetime import timedelta

import holidays
from django.db import transaction
from django.utils import timezone

from assignment.models import ScheduleAssignment
from shift.models import Shift

# 🇫🇷 calendrier jours fériés France
FR_HOLIDAYS = holidays.country_holidays("FR")


def is_french_holiday(date):
    """
    Retourne True si la date est un jour férié en France.
    """
    return date in FR_HOLIDAYS


@transaction.atomic
def generate_shifts_for_assignment(
    assignment: ScheduleAssignment,
    include_holidays: bool = False,
):
    if not assignment.is_active:
        return []

    week_pattern = assignment.week_pattern
    contract = assignment.contract
    user = contract.user

    start_date = assignment.start_date
    end_date = assignment.end_date or timezone.now().date()

    created_shifts = []

    # 🔹 précharger slots par jour
    slots_by_weekday = {
        day: list(
            week_pattern.time_slots.filter(
                weekday=day,
                slot_type="WORK",
            )
        )
        for day in range(7)
    }

    current_date = start_date

    while current_date <= end_date:
        # 🔹 jours fériés
        if is_french_holiday(current_date):
            if include_holidays:
                Shift.objects.get_or_create(
                    user=user,
                    assignment=assignment,
                    date=current_date,
                    shift_type="HOLIDAY",
                    start_time=None,
                    end_time=None,
                )
            current_date += timedelta(days=1)
            continue

        weekday = current_date.weekday()
        slots = slots_by_weekday.get(weekday, [])

        for slot in slots:
            shift, created = Shift.objects.get_or_create(
                user=user,
                assignment=assignment,
                date=current_date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                defaults={"shift_type": "WORK"},
            )

            if created:
                created_shifts.append(shift)

        current_date += timedelta(days=1)

    return created_shifts
