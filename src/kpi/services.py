from django.utils import timezone

from clock_event.models import ClockEvent
from shift.models import Shift


def get_attendance_kpis(
    *,
    date_from=None,
    date_to=None,
    user=None,
    team=None,
    department=None,
):
    """
    Retourne les KPI de présence.
    """

    shifts = Shift.objects.filter(shift_type=Shift.ShiftType.WORK)

    # ───────── FILTRES
    if date_from:
        shifts = shifts.filter(date__gte=date_from)

    if date_to:
        shifts = shifts.filter(date__lte=date_to)

    if user:
        shifts = shifts.filter(user=user)

    if team:
        shifts = shifts.filter(user__teams=team)

    if department:
        shifts = shifts.filter(user__teams__department=department)

    shifts = shifts.distinct()

    # ───────── BASE COUNTS
    planned_shifts = shifts.count()

    # Shifts avec au moins un CLOCK_IN approuvé
    worked_shift_ids = (
        ClockEvent.objects.filter(
            shift__in=shifts,
            event_type=ClockEvent.EventType.CLOCK_IN,
            status=ClockEvent.Status.APPROVED,
        )
        .values_list("shift_id", flat=True)
        .distinct()
    )

    worked_shifts = len(worked_shift_ids)

    attendance_rate = (worked_shifts / planned_shifts) * 100 if planned_shifts else 0

    # ───────── RETARDS
    # On compare la time part du timestamp avec shift.start_time
    # On récupère les CLOCK_IN approuvés et on filtre en Python
    clock_ins = ClockEvent.objects.filter(
        shift__in=shifts,
        event_type=ClockEvent.EventType.CLOCK_IN,
        status=ClockEvent.Status.APPROVED,
    ).select_related("shift")

    late_count = sum(
        1
        for e in clock_ins
        if e.shift.start_time
        and e.timestamp.astimezone(timezone.get_current_timezone()).time()
        > e.shift.start_time
    )

    # ───────── TEMPS TRAVAILLÉ
    # Pour chaque shift, on cherche le CLOCK_IN et le CLOCK_OUT approuvés
    clock_events_by_shift = {}
    for event in ClockEvent.objects.filter(
        shift__in=shifts,
        status=ClockEvent.Status.APPROVED,
        event_type__in=[ClockEvent.EventType.CLOCK_IN, ClockEvent.EventType.CLOCK_OUT],
    ).select_related("shift"):
        sid = event.shift_id
        if sid not in clock_events_by_shift:
            clock_events_by_shift[sid] = {}
        clock_events_by_shift[sid][event.event_type] = event.timestamp

    total_worked_seconds = 0
    for sid, events in clock_events_by_shift.items():
        clock_in = events.get(ClockEvent.EventType.CLOCK_IN)
        clock_out = events.get(ClockEvent.EventType.CLOCK_OUT)
        if clock_in and clock_out and clock_out > clock_in:
            total_worked_seconds += (clock_out - clock_in).total_seconds()

    # ───────── SHIFTS INCOMPLETS
    # A un CLOCK_IN approuvé mais pas de CLOCK_OUT approuvé
    clock_out_shift_ids = set(
        ClockEvent.objects.filter(
            shift__in=shifts,
            event_type=ClockEvent.EventType.CLOCK_OUT,
            status=ClockEvent.Status.APPROVED,
        )
        .values_list("shift_id", flat=True)
        .distinct()
    )

    clock_in_shift_ids = set(worked_shift_ids)

    incomplete_shifts = len(clock_in_shift_ids - clock_out_shift_ids)

    # ───────── SHIFTS MANQUÉS
    # Aucun CLOCK_IN approuvé
    missed_shifts = planned_shifts - len(
        shifts.filter(pk__in=clock_in_shift_ids).distinct()
    )

    # ───────── STATUT DU JOUR
    today = timezone.localdate()
    today_shift = shifts.filter(date=today).first()

    today_status = None
    if today_shift:
        events = {
            e.event_type: e.status
            for e in today_shift.clock_events.filter(status=ClockEvent.Status.APPROVED)
        }
        if ClockEvent.EventType.CLOCK_OUT in events:
            today_status = "COMPLETED"
        elif ClockEvent.EventType.CLOCK_IN in events:
            today_status = "IN_PROGRESS"
        else:
            today_status = "PLANNED"

    return {
        "planned_shifts": planned_shifts,
        "worked_shifts": worked_shifts,
        "attendance_rate": round(attendance_rate, 2),
        "late_count": late_count,
        "worked_seconds": int(total_worked_seconds),
        "incomplete_shifts": incomplete_shifts,
        "missed_shifts": missed_shifts,
        "today_status": today_status,
    }
