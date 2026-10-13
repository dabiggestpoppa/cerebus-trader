"""Named-timezone clock identities and session math (Ch III.1.3).

``ClockIdentity`` is a first-class, versioned, serializable value
(cross-model invariant #1): (timezone rule, DST policy, rule epoch,
registry version).  Two kinds exist:

* ``NAMED_IANA`` — stdlib ``zoneinfo`` with ``IANA_DST`` policy.  Used
  for every live/session calculation; it carries **no** fixed UTC offset
  (``utc_offset_minutes`` is ``None``) so no fixed-offset arithmetic can
  creep into the named-zone path (C1).
* ``FIXED_OFFSET`` — a research artifact that used fixed EST/no-DST time
  keeps an ``EST_NO_DST``-style identity forever; conversions never
  reinterpret it as ``America/New_York`` (C2).

Session math is performed by converting *naive wall times* through the
clock identity, so spring-forward gap hours, fall-back repeated hours
and sessions crossing DST boundaries resolve deterministically via
``fold``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .errors import ConventionViolationError, UnsupportedClockError

CLOCK_REGISTRY_VERSION = "CLOCK_REGISTRY_V1"


class ClockKind(str, Enum):
    NAMED_IANA = "NAMED_IANA"
    FIXED_OFFSET = "FIXED_OFFSET"


class DstPolicy(str, Enum):
    IANA_DST = "IANA_DST"
    NO_DST = "NO_DST"


@dataclass(frozen=True)
class ClockIdentity:
    """Versioned clock identity that travels with every derived value."""

    clock_id: str
    kind: ClockKind
    dst_policy: DstPolicy
    timezone_rule: str          # IANA zone name, or offset text for fixed
    utc_offset_minutes: int | None  # None for named zones (never hardcoded)
    rule_epoch: str             # rule-set vintage (e.g. TZDB epoch / artifact id)
    registry_version: str = CLOCK_REGISTRY_VERSION

    def __post_init__(self) -> None:
        if not self.clock_id:
            raise ConventionViolationError("clock_id required")
        if self.kind is ClockKind.NAMED_IANA:
            if self.dst_policy is not DstPolicy.IANA_DST:
                raise ConventionViolationError("named clock requires IANA_DST policy")
            if self.utc_offset_minutes is not None:
                raise ConventionViolationError(
                    "named clock must not carry a fixed utc offset"
                )
            if self.timezone_rule != self.clock_id:
                raise ConventionViolationError(
                    "named clock timezone_rule must equal its IANA id"
                )
        else:
            if self.dst_policy is not DstPolicy.NO_DST:
                raise ConventionViolationError("fixed clock requires NO_DST policy")
            if self.utc_offset_minutes is None:
                raise ConventionViolationError("fixed clock requires utc offset")

    @property
    def registry_version_value(self) -> str:
        return self.registry_version

    def zoneinfo(self) -> ZoneInfo:
        if self.kind is not ClockKind.NAMED_IANA:
            raise UnsupportedClockError(
                f"{self.clock_id} is a fixed-offset artifact, not a named zone"
            )
        return ZoneInfo(self.timezone_rule)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ClockIdentity":
        return cls(
            clock_id=data["clock_id"],
            kind=ClockKind(data["kind"]),
            dst_policy=DstPolicy(data["dst_policy"]),
            timezone_rule=data["timezone_rule"],
            utc_offset_minutes=data["utc_offset_minutes"],
            rule_epoch=data["rule_epoch"],
            registry_version=data["registry_version"],
        )


def named_clock(iana_name: str, *, rule_epoch: str = "TZDB_PLATFORM") -> ClockIdentity:
    """Build a named IANA clock; unknown zones fail closed."""
    try:
        ZoneInfo(iana_name)
    except (ZoneInfoNotFoundError, ValueError, KeyError, OSError):
        raise UnsupportedClockError(f"unknown IANA zone {iana_name!r}") from None
    return ClockIdentity(
        clock_id=iana_name,
        kind=ClockKind.NAMED_IANA,
        dst_policy=DstPolicy.IANA_DST,
        timezone_rule=iana_name,
        utc_offset_minutes=None,
        rule_epoch=rule_epoch,
    )


def fixed_clock(
    clock_id: str, offset_minutes: int, *, rule_epoch: str = "EST_FIXED_NO_DST_V1"
) -> ClockIdentity:
    """Build a fixed-offset artifact clock (never DST, never named-zone)."""
    sign = "-" if offset_minutes < 0 else "+"
    magnitude = abs(offset_minutes)
    offset_text = f"{sign}{magnitude // 60:02d}:{magnitude % 60:02d}"
    return ClockIdentity(
        clock_id=clock_id,
        kind=ClockKind.FIXED_OFFSET,
        dst_policy=DstPolicy.NO_DST,
        timezone_rule=offset_text,
        utc_offset_minutes=offset_minutes,
        rule_epoch=rule_epoch,
    )


def to_utc(
    local_wall_time: datetime, clock: ClockIdentity, *, fold: int = 0
) -> datetime:
    """Convert a naive wall time through the clock identity to aware UTC.

    ``fold=0``/``fold=1`` select the first/second occurrence inside a
    repeated (fall-back) hour; the default is deterministic and stable
    across calls.  Naive wall time is mandatory — mixing aware values
    here would hide the clock identity.
    """
    if local_wall_time.tzinfo is not None:
        raise ConventionViolationError("wall time must be naive; clock selects zone")
    if clock.kind is ClockKind.NAMED_IANA:
        aware = local_wall_time.replace(tzinfo=clock.zoneinfo(), fold=fold)
    else:
        assert clock.utc_offset_minutes is not None
        aware = local_wall_time.replace(
            tzinfo=timezone(timedelta(minutes=clock.utc_offset_minutes))
        )
    return aware.astimezone(timezone.utc)


def local_wall(instant_utc: datetime, clock: ClockIdentity) -> datetime:
    """Convert an aware UTC instant back to naive wall time on the clock."""
    if instant_utc.tzinfo is None:
        raise ConventionViolationError("instant must be tz-aware UTC")
    instant = instant_utc.astimezone(timezone.utc)
    if clock.kind is ClockKind.NAMED_IANA:
        return instant.astimezone(clock.zoneinfo()).replace(tzinfo=None)
    assert clock.utc_offset_minutes is not None
    return (instant + timedelta(minutes=clock.utc_offset_minutes)).replace(tzinfo=None)


def session_bounds_utc(
    day: date, start: time, end: time, clock: ClockIdentity, *, fold: int = 0
) -> tuple[datetime, datetime]:
    """UTC (start, end) instants of a wall-time session on ``day``.

    A session whose end wall time is not after its start wall time runs
    past midnight into the following calendar day.  Both edges are
    converted through the clock identity, so a DST transition inside the
    session changes the elapsed UTC duration without changing the wall
    construction.
    """
    start_local = datetime.combine(day, start)
    end_day = day if end > start else day + timedelta(days=1)
    end_local = datetime.combine(end_day, end)
    return (
        to_utc(start_local, clock, fold=fold),
        to_utc(end_local, clock, fold=fold),
    )
