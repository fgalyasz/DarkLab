from __future__ import annotations

GITHUB_REPO = "fgalyasz/DarkLab"
PACKAGE_NAME = "DarkLab"

MAC_ASSET = f"{PACKAGE_NAME}.dmg"
LINUX_ASSET = f"{PACKAGE_NAME}-linux-x86_64.tar.gz"
WINDOWS_ASSET = f"{PACKAGE_NAME}-windows-x64.zip"

PLATFORM_ASSETS = (
    ("macOS", MAC_ASSET),
    ("Linux", LINUX_ASSET),
    ("Windows", WINDOWS_ASSET),
)


def release_tag(version: str) -> str:
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid semver: {version}")
    return f"v{version}"


def download_url(tag: str, asset_name: str) -> str:
    return f"https://github.com/{GITHUB_REPO}/releases/download/{tag}/{asset_name}"


def release_notes(version: str) -> str:
    return (
        f"DarkLab {version} installers for macOS, Linux, and Windows. "
        "The macOS image is signed for the build and is not notarized."
    )


def gateway_html(version: str, assets: list[tuple[str, str]]) -> str:
    tag = release_tag(version)
    links = "\n".join(
        f'  <p><a href="{download_url(tag, filename)}">Download {label} ({filename})</a></p>'
        for label, filename in assets
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{PACKAGE_NAME} {version}</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; max-width: 36rem; margin: 4rem auto; padding: 0 1.25rem; color: #1c1917; }}
    a {{ color: #9a3412; }}
  </style>
</head>
<body>
  <h1>{PACKAGE_NAME}</h1>
  <p>Version {version}</p>
{links}
  <p>macOS image is signed for the build and is not notarized. Linux and Windows bundles are unsigned.</p>
</body>
</html>
"""


def platforms_for_paths(dist: dict[str, bool]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for label, filename in PLATFORM_ASSETS:
        if dist.get(filename):
            rows.append((label, filename))
    return rows
