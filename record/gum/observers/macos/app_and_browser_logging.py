from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    import Quartz 
except Exception: 
    Quartz = None

try:
    from AppKit import NSWorkspace 
except Exception: 
    NSWorkspace = None


__all__ = [
    "MacOSAppAndBrowserInspector",
    "check_automation_permission_granted",
]


SYSTEM_WINDOW_OWNERS = {"dock", "windowserver", "window server"}
OVERLAY_WINDOW_OWNERS = {
    "control center",
    "notification center",
    "notificationcentre",
    "notificationcentreui",
    "screen recording",
    "screenrecording",
    "screenrecordingindicator",
    "screenrecordingui",
    "screencapture",
    "screenshotui",
    "siri",
}

BROWSER_OSA_SCRIPTS: dict[str, tuple[str, ...]] = {
    "safari": (
        'tell application "Safari" to if (exists front document) then get URL of front document',
        'tell application "Safari" to if (count of documents) > 0 then get URL of front document',
        'jxa:(() => {\n  const safari = Application("Safari");\n  if (!safari.running()) { return null; }\n  const docs = safari.documents();\n  return docs.length ? docs[0].url() : null;\n})();',
    ),
    "safari technology preview": (
        'tell application "Safari Technology Preview" to if (exists front document) then get URL of front document',
        'jxa:(() => {\n  const safari = Application("Safari Technology Preview");\n  if (!safari.running()) { return null; }\n  const docs = safari.documents();\n  return docs.length ? docs[0].url() : null;\n})();',
    ),
    "google chrome": (
        'tell application "Google Chrome" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "google chrome beta": (
        'tell application "Google Chrome Beta" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "google chrome dev": (
        'tell application "Google Chrome Dev" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "google chrome canary": (
        'tell application "Google Chrome Canary" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "chromium": (
        'tell application "Chromium" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "brave browser": (
        'tell application "Brave Browser" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "brave browser beta": (
        'tell application "Brave Browser Beta" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "brave browser nightly": (
        'tell application "Brave Browser Nightly" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "microsoft edge": (
        'tell application "Microsoft Edge" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "microsoft edge beta": (
        'tell application "Microsoft Edge Beta" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "microsoft edge dev": (
        'tell application "Microsoft Edge Dev" to if (count of windows) > 0 then get URL of active tab of front window',
    ),
    "arc": (
        'tell application "Arc"\nif (count of windows) = 0 then return missing value\nreturn URL of active tab of front window\nend tell',
        'tell application "Arc"\nif (count of windows) = 0 then return missing value\ntell front window to tell active tab to return URL\nend tell',
        'jxa:(() => {\n  const arc = Application("Arc");\n  const wins = arc.windows();\n  if (!wins.length) { return null; }\n  const front = arc.frontWindow();\n  if (!front) { return null; }\n  const tab = front.activeTab();\n  return tab ? tab.url() : null;\n})();',
    ),
}

BROWSER_BUNDLE_IDS: dict[str, str] = {
    "com.apple.safari": "safari",
    "com.apple.safaritechnologypreview": "safari technology preview",
    "com.google.chrome": "google chrome",
    "com.google.chrome.beta": "google chrome beta",
    "com.google.chrome.dev": "google chrome dev",
    "com.google.chrome.canary": "google chrome canary",
    "org.chromium.chromium": "chromium",
    "com.brave.browser": "brave browser",
    "com.brave.browser.beta": "brave browser beta",
    "com.brave.browser.nightly": "brave browser nightly",
    "com.microsoft.edgemac": "microsoft edge",
    "com.microsoft.edgemac.beta": "microsoft edge beta",
    "com.microsoft.edgemac.dev": "microsoft edge dev",
    "company.thebrowser.browser": "arc",
}



AUTOMATION_PERMISSION_CACHE_TTL = 3.0
_AUTOMATION_PERMISSION_CACHE: tuple[float, bool | None] | None = None
_AUTOMATION_DENIED_SUBSTRINGS = (
    "-1743",
    "not authorized to send apple events",
    "not authorised to send apple events",
    "errae eventnotpermitted",
)


def _update_automation_cache(value: bool | None) -> None:
    global _AUTOMATION_PERMISSION_CACHE
    _AUTOMATION_PERMISSION_CACHE = (time.monotonic(), value)


def _read_automation_cache(force_refresh: bool = False) -> tuple[bool | None, bool]:
    if force_refresh:
        return None, False
    cache = _AUTOMATION_PERMISSION_CACHE
    if cache is None:
        return None, False
    ts, value = cache
    if time.monotonic() - ts <= AUTOMATION_PERMISSION_CACHE_TTL:
        return value, True
    return None, False


def _automation_denied_from_stderr(stderr: str) -> bool:
    if not stderr:
        return False
    if "-1743" in stderr:
        return True
    lowered = stderr.lower()
    return any(token in lowered for token in _AUTOMATION_DENIED_SUBSTRINGS)


def check_automation_permission_granted(force_refresh: bool = False) -> bool | None:
    cached_value, cache_hit = _read_automation_cache(force_refresh)
    if cache_hit:
        return cached_value

    inspector = MacOSAppAndBrowserInspector(logging.getLogger("gum.automation_probe"))
    running = inspector.running_browser_applications()

    denied_detected = False
    attempted = False

    for app_name, key, bundle_id in running:
        attempted = True
        inspector.last_frontmost_bundle_id = bundle_id
        result = inspector._run_browser_scripts(app_name, key)
        if result is not None:
            return True

        cached_value, cache_hit = _read_automation_cache()
        if cache_hit and cached_value is False:
            denied_detected = True
            break

    if denied_detected:
        return False

    if attempted:
        _update_automation_cache(None)
    return None




@dataclass
class MacOSAppAndBrowserInspector:
    logger: logging.Logger
    last_frontmost_bundle_id: Optional[str] = None
    unknown_browser_apps: set[str] = field(default_factory=set)
    browser_script_failures: set[tuple[str, str, int]] = field(default_factory=set)
    automation_denied_for: set[str] = field(default_factory=set)

    def get_frontmost_app_name(self) -> Optional[str]:
        if NSWorkspace is not None:
            try:
                app = NSWorkspace.sharedWorkspace().frontmostApplication()
                if app is not None:
                    bundle_id = (app.bundleIdentifier() or "").strip() or None
                    self.last_frontmost_bundle_id = bundle_id.lower() if bundle_id else None
                    name = (app.localizedName() or bundle_id or "").strip()
                    if name:
                        return name
            except Exception:
                self.last_frontmost_bundle_id = None

        if Quartz is None:
            self.last_frontmost_bundle_id = None
            return None

        try:
            opts = (
                Quartz.kCGWindowListOptionOnScreenOnly
                | Quartz.kCGWindowListOptionIncludingWindow
            )
            wins = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID) or []
        except Exception:
            self.last_frontmost_bundle_id = None
            return None

        self.last_frontmost_bundle_id = None
        candidate_name: Optional[str] = None
        candidate_area = 0

        for info in wins:
            owner = info.get("kCGWindowOwnerName") or ""
            owner_lower = owner.lower()
            if not owner or owner_lower in SYSTEM_WINDOW_OWNERS or owner_lower in OVERLAY_WINDOW_OWNERS:
                continue

            layer = info.get("kCGWindowLayer", 0)
            if layer != 0:
                continue

            alpha = info.get("kCGWindowAlpha", 1)
            if alpha == 0:
                continue

            bounds = info.get("kCGWindowBounds") or {}
            width = bounds.get("Width", 0) or 0
            height = bounds.get("Height", 0) or 0
            area = max(int(width), 0) * max(int(height), 0)
            if area <= 0:
                continue

            if area > candidate_area:
                candidate_name = owner
                candidate_area = area

        if candidate_name:
            return candidate_name

        for info in wins:
            owner = info.get("kCGWindowOwnerName") or ""
            if owner and owner.lower() not in SYSTEM_WINDOW_OWNERS:
                return owner

        return None

    def get_browser_url(self, app_name: Optional[str]) -> Optional[str]:
        if not app_name:
            return None

        log = self.logger
        key = self._resolve_browser_key(app_name)
        if key is None:
            signature = f"{app_name}|{self.last_frontmost_bundle_id or ''}"
            if signature not in self.unknown_browser_apps:
                self.unknown_browser_apps.add(signature)
                log.info(
                    "No browser URL mapping available for '%s' (bundle=%s)",
                    app_name,
                    self.last_frontmost_bundle_id,
                )
            return None

        return self._run_browser_scripts(app_name, key)

    def _run_browser_scripts(self, app_name: str, key: str) -> Optional[str]:
        log = self.logger
        scripts = BROWSER_OSA_SCRIPTS.get(key, ())
        if not scripts:
            if key not in self.unknown_browser_apps:
                self.unknown_browser_apps.add(key)
                log.info("No AppleScript candidates registered for '%s'", key)
            return None

        try:
            for script in scripts:
                cmd = ["osascript"]
                if script.startswith("jxa:"):
                    body = script[4:]
                    cmd.extend(["-l", "JavaScript", "-e", body])
                else:
                    cmd.extend(["-e", script])

                out = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=0.75,
                    check=False,
                )
                stdout = (out.stdout or "").strip()
                if out.returncode == 0 and stdout:
                    _update_automation_cache(True)
                    return stdout

                failure_sig = (key, script, out.returncode)
                if failure_sig not in self.browser_script_failures:
                    self.browser_script_failures.add(failure_sig)
                    stderr = (out.stderr or "").strip()
                    if _automation_denied_from_stderr(stderr):
                        _update_automation_cache(False)
                        if key not in self.automation_denied_for:
                            self.automation_denied_for.add(key)
                            log.warning(
                                "Automation permission denied when querying '%s'. "
                                "Enable Gum Recorder (or osascript) in System Settings → Privacy & Security → Automation.",
                                app_name,
                            )
                        return None
                    level = logging.WARNING if out.returncode not in (0, -128) else logging.INFO
                    log.log(
                        level,
                        "Browser URL script failed for '%s' (key=%s, exit=%s, stderr=%s)",
                        app_name,
                        key,
                        out.returncode,
                        stderr,
                    )
            return None
        except FileNotFoundError:
            log.warning("'osascript' binary not found when attempting to read browser URL")
            return None
        except subprocess.TimeoutExpired:
            log.debug("Timed out while fetching browser URL for '%s'", app_name)
            return None
        except Exception as exc:
            log.debug("Unexpected error fetching browser URL for '%s': %s", app_name, exc)
            return None

    def running_browser_applications(self) -> list[tuple[str, str, str]]:
        if NSWorkspace is None:
            return []
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running = workspace.runningApplications()
        except Exception:
            return []

        seen: set[str] = set()
        result: list[tuple[str, str, str]] = []
        for app in running:
            try:
                bundle_id = (app.bundleIdentifier() or "").strip().lower()
                if not bundle_id:
                    continue
                key = BROWSER_BUNDLE_IDS.get(bundle_id)
                if not key or key in seen:
                    continue
                name = app.localizedName() or bundle_id
                seen.add(key)
                result.append((name, key, bundle_id))
            except Exception:
                continue
        return result

    def prime_automation_for_running_browsers(self) -> bool:
        log = self.logger
        granted = check_automation_permission_granted()
        if granted:
            log.debug("Automation permission already granted; skipping browser preflight")
            return True

        attempted = False
        for app_name, key, bundle_id in self.running_browser_applications():
            attempted = True
            previous_bundle = self.last_frontmost_bundle_id
            try:
                self.last_frontmost_bundle_id = bundle_id
                self._run_browser_scripts(app_name, key)
            finally:
                self.last_frontmost_bundle_id = previous_bundle

        if not attempted:
            frontmost = self.get_frontmost_app_name()
            if frontmost:
                key = self._resolve_browser_key(frontmost)
                if key:
                    self._run_browser_scripts(frontmost, key)
                    attempted = True
                else:
                    log.debug("Frontmost app '%s' is not a known browser for automation preflight", frontmost)
            else:
                log.debug("No running browsers detected when attempting automation preflight")

        return attempted

    def _resolve_browser_key(self, app_name: str) -> Optional[str]:
        normalized = " ".join(app_name.lower().replace(".app", "").split())
        if normalized in BROWSER_OSA_SCRIPTS:
            return normalized

        bundle = (self.last_frontmost_bundle_id or "").strip().lower()
        if bundle:
            if bundle in BROWSER_BUNDLE_IDS:
                return BROWSER_BUNDLE_IDS[bundle]
            parts = bundle.split('.')
            while len(parts) > 2:
                parts = parts[:-1]
                candidate = '.'.join(parts)
                if candidate in BROWSER_BUNDLE_IDS:
                    return BROWSER_BUNDLE_IDS[candidate]

        if normalized.endswith(" browser"):
            simplified = normalized[:-8]
            if simplified in BROWSER_OSA_SCRIPTS:
                return simplified

        return None
