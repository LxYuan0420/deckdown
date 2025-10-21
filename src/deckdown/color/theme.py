from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from lxml import etree
from pptx.dml.color import MSO_THEME_COLOR


SCHEMA_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


@dataclass(frozen=True)
class ThemeResolver:
    scheme: dict[str, str]

    @classmethod
    def from_presentation(cls, prs: Any) -> "ThemeResolver":  # noqa: ANN401
        mapping: dict[str, str] = {}
        try:
            pkg = prs.part.package
            for part in pkg.parts:  # type: ignore[attr-defined]
                # theme content type endswith 'theme+xml'
                if getattr(part, "content_type", "").endswith("theme+xml"):
                    xml = part.blob
                    root = etree.fromstring(xml)
                    ns = {"a": SCHEMA_A}
                    clr = root.xpath("//a:clrScheme", namespaces=ns)
                    if not clr:
                        continue
                    scheme = clr[0]
                    for key in (
                        "dk1",
                        "lt1",
                        "dk2",
                        "lt2",
                        "accent1",
                        "accent2",
                        "accent3",
                        "accent4",
                        "accent5",
                        "accent6",
                        "hlink",
                        "folHlink",
                    ):
                        node = scheme.find(f"{{{SCHEMA_A}}}{key}")
                        if node is None:
                            continue
                        # prefer srgbClr val; fallback to sysClr lastClr
                        srgb = node.find(f"{{{SCHEMA_A}}}srgbClr")
                        if srgb is not None and srgb.get("val"):
                            mapping[key] = f"#{srgb.get('val').upper()}"
                            continue
                        sys = node.find(f"{{{SCHEMA_A}}}sysClr")
                        if sys is not None and sys.get("lastClr"):
                            mapping[key] = f"#{sys.get('lastClr').upper()}"
            if not mapping:
                # default Office-like fallbacks to avoid crashes
                mapping = {
                    "dk1": "#000000",
                    "lt1": "#FFFFFF",
                    "dk2": "#1F497D",
                    "lt2": "#EEECE1",
                    "accent1": "#4F81BD",
                    "accent2": "#C0504D",
                    "accent3": "#9BBB59",
                    "accent4": "#8064A2",
                    "accent5": "#4BACC6",
                    "accent6": "#F79646",
                    "hlink": "#0000FF",
                    "folHlink": "#800080",
                }
        except Exception:
            mapping = {
                "dk1": "#000000",
                "lt1": "#FFFFFF",
            }
        return cls(mapping)

    def _key_from_theme_enum(self, theme_enum: Any) -> str | None:  # noqa: ANN401
        try:
            name = theme_enum.name  # MSO_THEME_COLOR enum
        except Exception:
            return None
        table = {
            "ACCENT_1": "accent1",
            "ACCENT_2": "accent2",
            "ACCENT_3": "accent3",
            "ACCENT_4": "accent4",
            "ACCENT_5": "accent5",
            "ACCENT_6": "accent6",
            "TEXT_1": "dk1",
            "TEXT_2": "dk2",
            "BACKGROUND_1": "lt1",
            "BACKGROUND_2": "lt2",
            "HYPERLINK": "hlink",
            "FOLLOWED_HYPERLINK": "folHlink",
        }
        return table.get(name)

    def color_dict_from_colorformat(self, cf: Any) -> dict | None:  # noqa: ANN401
        # Prefer theme color if present
        try:
            theme_enum = getattr(cf, "theme_color", None)
        except Exception:
            theme_enum = None
        key = self._key_from_theme_enum(theme_enum) if theme_enum else None
        if key:
            rgb = self.scheme.get(key)
            return {"resolved_rgb": rgb, "theme_ref": {"key": key}} if rgb else {"theme_ref": {"key": key}}
        # Fall back to explicit RGB if available
        try:
            rgb = getattr(cf, "rgb", None)
            if rgb is not None:
                return {"resolved_rgb": f"#{str(rgb)}"}
        except Exception:
            return None
        return None

