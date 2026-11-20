"""OWASP ZAP tool for authorized web scans."""

from collections import Counter
import json
import os
import time
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import ProxyHandler, build_opener

from dotenv import load_dotenv
from langchain.tools import tool

from ..paths import PROJECT_ROOT


class ZapError(RuntimeError):
    """Raised when the local ZAP service cannot complete a request."""


def _zap_api(
    base_url: str,
    component: str,
    operation_type: Literal["action", "view"],
    operation: str,
    api_key: str,
    timeout_seconds: float,
    **parameters: object,
) -> dict[str, object]:
    """Call one JSON endpoint on the local ZAP API."""
    query = {"apikey": api_key}
    query.update(
        {
            name: str(value).lower() if isinstance(value, bool) else str(value)
            for name, value in parameters.items()
            if value is not None
        }
    )
    url = (
        f"{base_url.rstrip('/')}/JSON/{component}/{operation_type}/{operation}/?"
        f"{urlencode(query)}"
    )
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(url, timeout=max(0.1, timeout_seconds)) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise ZapError(f"ZAP API returned HTTP {error.code}.") from error
    except URLError as error:
        raise ZapError(f"Could not reach ZAP at {base_url}: {error.reason}") from error
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ZapError(f"Invalid response from ZAP: {error}") from error
    if not isinstance(payload, dict):
        raise ZapError("ZAP returned an unexpected response format.")
    if "code" in payload and "message" in payload:
        raise ZapError(f"ZAP error {payload['code']}: {payload['message']}")
    return payload


def _remaining_timeout(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ZapError("ZAP scan exceeded its configured timeout.")
    return min(10.0, remaining)


def _wait_for_percentage(
    base_url: str,
    component: str,
    scan_id: str,
    api_key: str,
    deadline: float,
) -> None:
    while True:
        response = _zap_api(
            base_url,
            component,
            "view",
            "status",
            api_key,
            _remaining_timeout(deadline),
            scanId=scan_id,
        )
        try:
            progress = int(str(response["status"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ZapError(f"ZAP returned no valid {component} progress value.") from error
        if progress >= 100:
            return
        time.sleep(min(2.0, _remaining_timeout(deadline)))


def _wait_for_passive_scan(base_url: str, api_key: str, deadline: float) -> None:
    while True:
        response = _zap_api(
            base_url,
            "pscan",
            "view",
            "recordsToScan",
            api_key,
            _remaining_timeout(deadline),
        )
        try:
            remaining = int(str(response["recordsToScan"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ZapError("ZAP returned no valid passive-scan queue size.") from error
        if remaining <= 0:
            return
        time.sleep(min(2.0, _remaining_timeout(deadline)))


def _validated_zap_target(target_url: str, allowed_hosts: set[str]) -> str:
    if not isinstance(target_url, str) or not target_url.strip():
        raise ZapError("target_url must be a non-empty URL.")
    if any(character in target_url for character in ("\x00", "\r", "\n")):
        raise ZapError("target_url must be a single-line URL.")
    parsed = urlsplit(target_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ZapError("target_url must be an absolute HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise ZapError("Credentials must not be embedded in target_url.")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname not in allowed_hosts:
        raise ZapError(
            f"Target host '{hostname}' is not in ZAP_ALLOWED_HOSTS. "
            "Add it to .env only after confirming that the target is authorized."
        )
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))


def _format_zap_result(
    target_url: str,
    scan_mode: str,
    alerts: list[object],
    max_alerts: int,
) -> str:
    normalized_alerts = [alert for alert in alerts if isinstance(alert, dict)]
    risk_counts = Counter(str(alert.get("risk", "Unknown")) for alert in normalized_alerts)
    selected = []
    for alert in normalized_alerts[:max_alerts]:
        selected.append(
            {
                "risk": alert.get("risk"),
                "confidence": alert.get("confidence"),
                "name": alert.get("alert"),
                "url": alert.get("url"),
                "parameter": alert.get("param"),
                "plugin_id": alert.get("pluginId"),
                "description": alert.get("description"),
                "solution": alert.get("solution"),
            }
        )
    return json.dumps(
        {
            "status": "completed",
            "target": target_url,
            "scan_mode": scan_mode,
            "alert_count": len(normalized_alerts),
            "risk_counts": dict(sorted(risk_counts.items())),
            "returned_alerts": len(selected),
            "alerts_truncated": len(normalized_alerts) > len(selected),
            "alerts": selected,
        },
        ensure_ascii=False,
    )


def _zap_scan_impl(
    target_url: str,
    scan_mode: Literal["passive", "active"] = "passive",
    authorization_confirmed: bool = False,
    timeout_seconds: int = 600,
    max_alerts: int = 50,
) -> str:
    if scan_mode not in {"passive", "active"}:
        return "Error: scan_mode must be 'passive' or 'active'."
    if scan_mode == "active" and not authorization_confirmed:
        return (
            "Error: active scans require authorization_confirmed=true after the user "
            "explicitly confirms ownership or permission for the target."
        )
    if not 30 <= timeout_seconds <= 3600:
        return "Error: timeout_seconds must be between 30 and 3600."
    if not 1 <= max_alerts <= 500:
        return "Error: max_alerts must be between 1 and 500."

    load_dotenv(PROJECT_ROOT / ".env")
    base_url = os.getenv("ZAP_BASE_URL", "http://127.0.0.1:8090").strip()
    api_key = os.getenv("ZAP_API_KEY", "").strip()
    allowed_hosts_text = os.getenv(
        "ZAP_ALLOWED_HOSTS", "host.docker.internal,localhost,127.0.0.1"
    )
    allowed_hosts = {
        host.strip().lower().rstrip(".")
        for host in allowed_hosts_text.split(",")
        if host.strip()
    }
    if not api_key:
        return "Error: ZAP_API_KEY is not configured in .env."
    try:
        target = _validated_zap_target(target_url, allowed_hosts)
        deadline = time.monotonic() + timeout_seconds
        spider = _zap_api(
            base_url,
            "spider",
            "action",
            "scan",
            api_key,
            _remaining_timeout(deadline),
            url=target,
            recurse=True,
        )
        scan_id = str(spider["scan"])
        _wait_for_percentage(base_url, "spider", scan_id, api_key, deadline)
        _wait_for_passive_scan(base_url, api_key, deadline)

        if scan_mode == "active":
            active_scan = _zap_api(
                base_url,
                "ascan",
                "action",
                "scan",
                api_key,
                _remaining_timeout(deadline),
                url=target,
                recurse=True,
            )
            active_scan_id = str(active_scan["scan"])
            _wait_for_percentage(base_url, "ascan", active_scan_id, api_key, deadline)
            _wait_for_passive_scan(base_url, api_key, deadline)

        alert_response = _zap_api(
            base_url,
            "core",
            "view",
            "alerts",
            api_key,
            _remaining_timeout(deadline),
            baseurl=target,
            start=0,
            count=5000,
        )
        alerts = alert_response.get("alerts", [])
        if not isinstance(alerts, list):
            raise ZapError("ZAP returned an invalid alerts list.")
        return _format_zap_result(target, scan_mode, alerts, max_alerts)
    except (KeyError, ZapError) as error:
        return f"Error: {error}"


@tool
def zap_scan(
    target_url: str,
    scan_mode: Literal["passive", "active"] = "passive",
    authorization_confirmed: bool = False,
    timeout_seconds: int = 600,
    max_alerts: int = 50,
) -> str:
    """Scannt ein Webziel mit dem lokalen OWASP-ZAP-Dienst.

    ``passive`` crawlt das Ziel mit ZAPs herkömmlichem Spider und wartet
    anschließend die passive Analyse ab.
    ``active`` sendet zusätzlich Angriffstest-Payloads und kann den
    Anwendungszustand verändern. Setze dann ``authorization_confirmed`` auf true.
    Der Ziel-Hostname muss außerdem in ``ZAP_ALLOWED_HOSTS`` in der .env-Datei
    aufgeführt sein.

    Für eine Webanwendung, die vom Windows-Host aus Docker erreichbar ist,
    verwende eine URL wie ``http://host.docker.internal:3000`` statt localhost.
    ``timeout_seconds`` begrenzt die Laufzeit des gesamten Ablaufs. Das Ergebnis
    ist JSON mit der Anzahl der Befunde je Risiko sowie bis zu ``max_alerts``
    detaillierten Befunden.
    """
    return _zap_scan_impl(
        target_url=target_url,
        scan_mode=scan_mode,
        authorization_confirmed=authorization_confirmed,
        timeout_seconds=timeout_seconds,
        max_alerts=max_alerts,
    )
