"""Plain-language knowledge about incident types: titles and recommended actions."""

import zlib

_GENERIC = ["Investigate the source IP in your SIEM", "Review related events in the live stream", "Escalate if the activity continues"]

PLAYBOOK = {
    "login_failed": ("Brute-force login attempts", [
        "Block the source IP at the firewall", "Enforce MFA and account lockout on the targeted account",
        "Check authentication logs for a successful login from this IP"]),
    "login_success": ("Suspicious login", [
        "Verify the login with the account owner", "Reset the password and revoke active sessions",
        "Check for logins from other countries within a short time"]),
    "port_scan": ("Port scan detected", [
        "Block the scanning IP", "Close or firewall ports that should not be exposed", "Enable rate limiting on the perimeter"]),
    "firewall_deny": ("Blocked connection burst", [
        "Confirm the firewall is dropping this traffic", "Block the source IP upstream", "Watch for the same source on other hosts"]),
    "file_transfer": ("Large outbound data transfer", [
        "Check the destination IP and the user's intent", "Suspend the user's network access until verified",
        "Review data-loss-prevention logs for what was sent"]),
    "privilege_escalation": ("Privilege escalation", [
        "Terminate the elevated session", "Audit what was run with elevated rights", "Rotate credentials for the affected account"]),
    "file_access": ("Sensitive data access", [
        "Identify what data was opened or dumped", "Restrict access for this account", "Review database and file-server audit logs"]),
}


def title_for(event_type: str) -> str:
    return PLAYBOOK.get(event_type, (f"Anomalous {event_type.replace('_', ' ')}", _GENERIC))[0]


def actions_for(event_type: str) -> list[str]:
    return PLAYBOOK.get(event_type, ("", _GENERIC))[1]


def incident_id(source_ip: str, event_type: str) -> str:
    return f"INC-{zlib.crc32(f'{source_ip}|{event_type}'.encode()) % 100000:05d}"
