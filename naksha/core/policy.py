"""Role-based access control and jurisdiction policy table for NAKSHA.

TODO: verify statutory jurisdictional rules with Ministry of Land source.
"""
from typing import Set, Optional
from naksha.models.auth import OfficerRole, OfficerContext

# Policy Table: Allowed roles per route group
# TODO: verify statutory jurisdictional rules with Ministry of Land source.
ROUTE_ROLE_POLICIES: dict[str, Set[OfficerRole]] = {
    # Land Records access: Union Land Officer, AC Land, Kanungo, Surveyor
    "records": {
        OfficerRole.UNION_LAND_OFFICER,
        OfficerRole.AC_LAND,
        OfficerRole.KANUNGO,
        OfficerRole.SURVEYOR,
        OfficerRole.SYSTEM_ADMIN,
    },
    # Spatial & Verification operations: ULO, AC Land, Kanungo
    "spatial": {
        OfficerRole.UNION_LAND_OFFICER,
        OfficerRole.AC_LAND,
        OfficerRole.KANUNGO,
        OfficerRole.SYSTEM_ADMIN,
    },
    # Trust Ledger audit inspection: AC Land, Kanungo, Admin
    "ledger": {
        OfficerRole.AC_LAND,
        OfficerRole.KANUNGO,
        OfficerRole.SYSTEM_ADMIN,
    },
}


def check_role_permission(role: OfficerRole, route_group: str) -> bool:
    """Checks whether the given role is authorized for the requested route group."""
    allowed = ROUTE_ROLE_POLICIES.get(route_group, set())
    return role in allowed or role == OfficerRole.SYSTEM_ADMIN


def check_jurisdiction_permission(context: OfficerContext, target_mouza: Optional[str]) -> bool:
    """Checks whether the officer's jurisdiction permits accessing target mouza.

    Rules:
    - SYSTEM_ADMIN has global scope.
    - AC_LAND has upazila-wide jurisdiction (e.g. গাজীপুর সদর, covers all constituent mouzas).
    - UNION_LAND_OFFICER and KANUNGO are scoped to their assigned jurisdiction (e.g. কাশিমপুর).
    
    TODO: verify statutory jurisdictional rules with Ministry of Land source.
    """
    if context.role == OfficerRole.SYSTEM_ADMIN:
        return True

    if not target_mouza or target_mouza == "Unknown":
        # Missing or unspecified parcel jurisdiction allowed for general queries
        return True

    clean_target = target_mouza.lower().strip()
    clean_scope = context.jurisdiction.lower().strip()

    # AC Land covers the whole upazila (e.g. Gazipur Sadar / কাশিমপুর is within Gazipur Sadar)
    if context.role == OfficerRole.AC_LAND:
        return True

    # Union Land Officer and Kanungo must match their assigned mouza / jurisdiction
    if clean_scope in clean_target or clean_target in clean_scope:
        return True

    # Check common English / Bengali names (e.g. Kashimpur vs কাশিমপুর)
    known_aliases = {
        "কাশিমপুর": ["kashimpur", "কাশিমপুর"],
        "গাজীপুর সদর": ["gazipur", "gazipur sadar", "গাজীপুর সদর"],
    }
    for key, aliases in known_aliases.items():
        if any(a in clean_scope for a in aliases) and any(a in clean_target for a in aliases):
            return True

    return False
