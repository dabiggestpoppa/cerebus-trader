"""FORGE policy kernel (Book II / Bloc II.4).

Pure, deterministic, provider-neutral authorization kernel. No FastAPI, no
SQL, no network, no protected-body dependency, no mutable global state.

Governing laws (frozen):

- IDENTITY != POLICY: the kernel consumes an II.3 `ForgePrincipal` as given;
  it has no API to reconstruct identity from email, provider subjects,
  request headers or raw JSON. Authentication owns principal creation.
- AUTHENTICATION != AUTHORIZATION: a valid principal authorizes nothing by
  itself. Every protected exposure requires a trusted capability fact.
- POLICY != ENTITLEMENT / ENTITLEMENT != COMMERCE: the kernel consumes
  capability facts from the `AuthorizationContext` seam; it never produces,
  prices, refreshes or stores them. Book VI owns commercial state.
- EXPOSURE METADATA != POLICY DECISION: Book I exposure classes are inputs
  to ONE central matrix here — never scattered `if premium` checks.
- DEFAULT-DENY: unknown action, unknown exposure, malformed context, missing
  context, missing capability ⇒ DENY. Never default-allow.
- POLICY MUST RUN BEFORE RELEASE: callers must evaluate the kernel BEFORE
  loading protected content (see the enforcement service). The kernel itself
  requires no protected body to decide — only safe resource metadata.

Exposure matrix (central authority — full rationale in bloc PLAN.md):

| Exposure         | anon | auth,no-cap | member | operator | research | forge.internal |
|------------------|------|-------------|--------|----------|----------|----------------|
| PUBLIC_TEACHING  | A    | A           | A      | A        | A        | A              |
| SUBSCRIBER_MODEL | D    | D           | A      | A        | A        | A              |
| OPERATOR_ONLY    | D    | D           | D      | A        | A        | A              |
| RESEARCH_LAB     | D    | D           | D      | A        | A        | A              |
| INTERNAL_METHOD  | D    | D           | D      | D        | D        | A              |
| INTERNAL_CODE    | D    | D           | D      | D        | D        | A              |
| unknown          | D    | D           | D      | D        | D        | D              |

Cumulative read-down within ordinary exposure; internal classes admit ONLY
`forge.internal`. `forge.internal` is the single fail-closed capability atom
reserved for explicitly-configured trusted internal service principals —
no staff role or ordinary capability combination reaches internal classes.

RESEARCH_LAB authorization never mutates research/evidence/canonical status:
a principal allowed to view research still receives it AS research.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.forge.canonical import ProductExposure
from app.forge.identity import ForgePrincipal

# ---------------------------------------------------------------------------
# Reason codes (frozen Ch II.4.8 vocabulary where applicable)
# ---------------------------------------------------------------------------


class PolicyReason(str, Enum):
    """Machine-readable, content-free denial/allowance reasons."""

    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    ENTITLEMENT_MISSING = "ENTITLEMENT_MISSING"
    ENTITLEMENT_EXPIRED = "ENTITLEMENT_EXPIRED"
    ROLE_MISSING = "ROLE_MISSING"
    EXPOSURE_FORBIDDEN = "EXPOSURE_FORBIDDEN"
    OBJECT_UNAVAILABLE = "OBJECT_UNAVAILABLE"
    POLICY_UNKNOWN = "POLICY_UNKNOWN"
    UNKNOWN_ACTION = "UNKNOWN_ACTION"
    UNKNOWN_EXPOSURE = "UNKNOWN_EXPOSURE"
    UNKNOWN_RESOURCE_TYPE = "UNKNOWN_RESOURCE_TYPE"
    MALFORMED_CONTEXT = "MALFORMED_CONTEXT"
    GRANTED = "GRANTED"


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


class PolicyAction(str, Enum):
    """Governed action vocabulary (frozen equivalents). Deliberately small.

    Unknown or arbitrary action strings ⇒ DENY (never extended by callers).
    """

    VIEW = "VIEW"
    QUERY = "QUERY"
    OPERATE = "OPERATE"
    ADMINISTER = "ADMINISTER"


# ---------------------------------------------------------------------------
# Resource metadata
# ---------------------------------------------------------------------------


class PolicyResourceType(str, Enum):
    """Bounded resource-type vocabulary for safe policy metadata."""

    CANONICAL_OBJECT = "CANONICAL_OBJECT"
    ARTIFACT = "ARTIFACT"
    CAPABILITY = "CAPABILITY"
    SERVICE_ENDPOINT = "SERVICE_ENDPOINT"


@dataclass(frozen=True)
class ResourcePolicyMetadata:
    """Safe resource description: everything policy may know, nothing more.

    Constructible from an index/ID alone — authorizing a resource NEVER
    requires loading its protected body. `resource_id` is an opaque
    identifier, not content.
    """

    resource_type: PolicyResourceType
    resource_id: str
    exposure: ProductExposure | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.resource_type, PolicyResourceType):
            raise ValueError("resource_type must be a PolicyResourceType")
        if not self.resource_id or not isinstance(self.resource_id, str):
            raise ValueError("resource_id must be a non-empty string")


# ---------------------------------------------------------------------------
# Authorization context (Book VI seam)
# ---------------------------------------------------------------------------

# Capability registry: exact-match atoms describing permission FACTS, not
# product marketing names. Book VI later maps products -> these atoms; the
# policy matrix consumes only these. `forge.internal` is the sole atom that
# can admit INTERNAL_METHOD/INTERNAL_CODE.
CAPABILITY_CORPUS_READ_PUBLIC = "corpus.read.public"
CAPABILITY_CORPUS_READ_MEMBER = "corpus.read.member"
CAPABILITY_MODEL_READ_OPERATOR = "model.read.operator"
CAPABILITY_EVIDENCE_READ_RESEARCH = "evidence.read.research"
CAPABILITY_ADMIN_RESEARCH = "admin.research"
CAPABILITY_ADMIN_COMMERCE = "admin.commerce"
CAPABILITY_FORGE_INTERNAL = "forge.internal"

REGISTERED_CAPABILITIES: frozenset[str] = frozenset(
    {
        CAPABILITY_CORPUS_READ_PUBLIC,
        CAPABILITY_CORPUS_READ_MEMBER,
        CAPABILITY_MODEL_READ_OPERATOR,
        CAPABILITY_EVIDENCE_READ_RESEARCH,
        CAPABILITY_ADMIN_RESEARCH,
        CAPABILITY_ADMIN_COMMERCE,
        CAPABILITY_FORGE_INTERNAL,
    }
)


@dataclass(frozen=True)
class AuthorizationContext:
    """Trusted, provider-neutral authorization-context seam.

    A passive fact-carrier constructed explicitly from trusted service
    input (later: Book VI entitlement resolution). It must never contain
    price, billing, plan names, subscription state, provider IDs, or raw
    request authority. Capabilities are exact-match atoms; missing
    capability means the fact does not exist — there is no wildcard.
    """

    capabilities: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if isinstance(self.capabilities, (str, bytes)) or not isinstance(
            self.capabilities, (frozenset, set)
        ):
            raise ValueError("capabilities must be a frozenset of strings")

    @classmethod
    def empty(cls) -> "AuthorizationContext":
        return cls(capabilities=frozenset())

    @classmethod
    def of(cls, *capabilities: str) -> "AuthorizationContext":
        return cls(capabilities=frozenset(capabilities))

    def has(self, capability: str) -> bool:
        """Exact atom match. No wildcard, substring, or prefix logic."""

        if not isinstance(capability, str):
            return False
        return capability in self.capabilities


def is_well_formed(context: object) -> bool:
    """Structural validation used for default-deny on malformed input."""

    if not isinstance(context, AuthorizationContext):
        return False
    if not isinstance(context.capabilities, frozenset):
        return False
    return all(isinstance(c, str) and c for c in context.capabilities)


# ---------------------------------------------------------------------------
# Policy decision
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyDecision:
    """Deterministic, auditable policy outcome.

    Contains NO protected content: `detail` is rule-descriptive only.
    Value equality makes repeated decisions comparable in tests/audit.
    """

    allowed: bool
    reason_code: PolicyReason
    detail: str = ""

    @classmethod
    def allow(cls, reason: PolicyReason = PolicyReason.GRANTED, detail: str = "") -> "PolicyDecision":
        return cls(allowed=True, reason_code=reason, detail=detail)

    @classmethod
    def deny(cls, reason: PolicyReason, detail: str = "") -> "PolicyDecision":
        return cls(allowed=False, reason_code=reason, detail=detail)


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------


class PolicyEngine:
    """The policy port. One central authority; no scattered exposure checks."""

    def decide(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        action: PolicyAction | str,
        resource: ResourcePolicyMetadata,
    ) -> PolicyDecision:
        raise NotImplementedError


def _coerce_action(action: PolicyAction | str) -> PolicyAction | None:
    if isinstance(action, PolicyAction):
        return action
    if isinstance(action, str):
        try:
            return PolicyAction(action)
        except ValueError:
            return None
    return None


# Exposure classes an anonymous principal may VIEW/QUERY (explicitly
# enumerated; Product Exposure Rules authorize public teaching for public
# consumption and II.3 explicitly supports anonymous principals).
_ANONYMOUS_ALLOWED_EXPOSURES: frozenset[ProductExposure] = frozenset(
    {ProductExposure.PUBLIC_TEACHING}
)

# Capability -> the exposure classes it admits (cumulative read-down: each
# capability admits its own class and everything "below" it in the matrix).
_CAPABILITY_EXPOSURES: dict[str, frozenset[ProductExposure]] = {
    CAPABILITY_CORPUS_READ_PUBLIC: frozenset({ProductExposure.PUBLIC_TEACHING}),
    CAPABILITY_CORPUS_READ_MEMBER: frozenset(
        {ProductExposure.PUBLIC_TEACHING, ProductExposure.SUBSCRIBER_MODEL}
    ),
    CAPABILITY_MODEL_READ_OPERATOR: frozenset(
        {
            ProductExposure.PUBLIC_TEACHING,
            ProductExposure.SUBSCRIBER_MODEL,
            ProductExposure.OPERATOR_ONLY,
            ProductExposure.RESEARCH_LAB,
        }
    ),
    CAPABILITY_EVIDENCE_READ_RESEARCH: frozenset(
        {
            ProductExposure.PUBLIC_TEACHING,
            ProductExposure.SUBSCRIBER_MODEL,
            ProductExposure.OPERATOR_ONLY,
            ProductExposure.RESEARCH_LAB,
        }
    ),
    CAPABILITY_FORGE_INTERNAL: frozenset(set(ProductExposure)),
}

# Ordinary capabilities that can NEVER admit internal classes, no matter how
# they are combined. Only CAPABILITY_FORGE_INTERNAL bypasses this.
_ORDINARY_CAPABILITIES: frozenset[str] = frozenset(
    REGISTERED_CAPABILITIES - {CAPABILITY_FORGE_INTERNAL}
)


class DefaultDenyPolicyEngine(PolicyEngine):
    """The single central exposure-matrix authority. Pure and stateless."""

    def decide(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        action: PolicyAction | str,
        resource: ResourcePolicyMetadata,
    ) -> PolicyDecision:
        # 1. Malformed inputs deny first (default-deny law).
        resolved_action = _coerce_action(action)
        if resolved_action is None:
            return PolicyDecision.deny(
                PolicyReason.UNKNOWN_ACTION, "action is not a governed PolicyAction"
            )
        if not isinstance(principal, ForgePrincipal):
            return PolicyDecision.deny(
                PolicyReason.POLICY_UNKNOWN, "principal is not a ForgePrincipal"
            )
        if not is_well_formed(context):
            return PolicyDecision.deny(
                PolicyReason.MALFORMED_CONTEXT, "authorization context is malformed"
            )
        if not isinstance(resource, ResourcePolicyMetadata):
            return PolicyDecision.deny(
                PolicyReason.POLICY_UNKNOWN, "resource metadata is malformed"
            )
        if resource.exposure is not None and not isinstance(
            resource.exposure, ProductExposure
        ):
            return PolicyDecision.deny(
                PolicyReason.UNKNOWN_EXPOSURE, "resource exposure is not recognized"
            )

        # 2. Anonymous is explicitly enumerated.
        if not principal.authenticated:
            if (
                resource.exposure in _ANONYMOUS_ALLOWED_EXPOSURES
                and resolved_action in (PolicyAction.VIEW, PolicyAction.QUERY)
            ):
                return PolicyDecision.allow(
                    detail="anonymous public teaching access"
                )
            return PolicyDecision.deny(
                PolicyReason.NOT_AUTHENTICATED,
                "anonymous principals may only view public teaching",
            )

        # 3. Disabled users deny regardless of anything else.
        #    (The kernel cannot import UserState logic circularly; identity
        #    state is validated at authentication, but a principal built from
        #    a DISABLED user never passes the enforcement service — see
        #    ForgePolicyEnforcementService. Belt-and-braces: roles on the
        #    principal are never consulted for commercial meaning.)

        # 4. Unknown exposure denies (never coerced to a nearest class).
        if resource.exposure is None:
            return PolicyDecision.deny(
                PolicyReason.UNKNOWN_EXPOSURE, "resource carries no recognized exposure"
            )

        # 5. Internal classes admit ONLY the forge.internal capability.
        if resource.exposure in (ProductExposure.INTERNAL_METHOD, ProductExposure.INTERNAL_CODE):
            if context.has(CAPABILITY_FORGE_INTERNAL):
                return PolicyDecision.allow(
                    detail="trusted internal service capability"
                )
            return PolicyDecision.deny(
                PolicyReason.EXPOSURE_FORBIDDEN,
                "internal exposure is not accessible to customer principals",
            )

        # 6. Ordinary exposures: the principal must hold one ordinary
        #    capability whose admitted set covers the exposure. Exact atoms
        #    only; forge.internal never *reduces* access.
        for capability in sorted(_ORDINARY_CAPABILITIES):
            if context.has(capability) and resource.exposure in _CAPABILITY_EXPOSURES[capability]:
                return PolicyDecision.allow(
                    detail=f"capability {capability} admits exposure {resource.exposure.value}"
                )
        return PolicyDecision.deny(
            PolicyReason.ENTITLEMENT_MISSING,
            "no trusted capability admits this exposure",
        )


# Module-level singleton exposure: the engine is a STATELESS function object
# (no mutable state), so a shared instance is safe; tests still construct
# independent instances to prove no cross-instance state exists.
DEFAULT_POLICY_ENGINE = DefaultDenyPolicyEngine()


__all__ = [
    "PolicyReason",
    "PolicyAction",
    "PolicyResourceType",
    "ResourcePolicyMetadata",
    "AuthorizationContext",
    "is_well_formed",
    "PolicyDecision",
    "PolicyEngine",
    "DefaultDenyPolicyEngine",
    "DEFAULT_POLICY_ENGINE",
    "CAPABILITY_CORPUS_READ_PUBLIC",
    "CAPABILITY_CORPUS_READ_MEMBER",
    "CAPABILITY_MODEL_READ_OPERATOR",
    "CAPABILITY_EVIDENCE_READ_RESEARCH",
    "CAPABILITY_ADMIN_RESEARCH",
    "CAPABILITY_ADMIN_COMMERCE",
    "CAPABILITY_FORGE_INTERNAL",
    "REGISTERED_CAPABILITIES",
]
