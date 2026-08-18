"""IPTC data model and preset management for image metadata."""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class IPTCData:
    """IPTC metadata container."""

    creator: str = ""  # Photographer name (Iptc.Application2.Writer)
    copyright: str = ""  # Copyright notice (Iptc.Application2.Copyright)
    credit: str = ""  # Credit line (Iptc.Application2.Credit)
    source: str = ""  # Source (Iptc.Application2.Source)
    keywords: list[str] = field(default_factory=list)  # Keywords (Iptc.Application2.Keywords)

    def to_dict(self) -> dict[str, object]:
        """Convert IPTC data to dictionary."""
        return {
            "creator": self.creator,
            "copyright": self.copyright,
            "credit": self.credit,
            "source": self.source,
            "keywords": self.keywords.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "IPTCData":
        """Create IPTC data from dictionary."""
        return cls(
            creator=str(data.get("creator", "")),
            copyright=str(data.get("copyright", "")),
            credit=str(data.get("credit", "")),
            source=str(data.get("source", "")),
            keywords=list(data.get("keywords", [])),
        )

    def get_keywords_text(self) -> str:
        """Get keywords as newline-separated text."""
        return "\n".join(self.keywords)

    def set_keywords_from_text(self, text: str) -> None:
        """Set keywords from newline-separated text."""
        self.keywords = [kw.strip() for kw in text.split("\n") if kw.strip()]


@dataclass
class IPTCPreset:
    """IPTC preset with name and data."""

    name: str
    data: IPTCData
    is_default: bool = False

    def to_dict(self) -> dict[str, object]:
        """Convert preset to dictionary."""
        return {
            "name": self.name,
            "data": self.data.to_dict(),
            "is_default": self.is_default,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "IPTCPreset":
        """Create preset from dictionary."""
        return cls(
            name=str(data.get("name", "")),
            data=IPTCData.from_dict(data.get("data", {})),
            is_default=bool(data.get("is_default", False)),
        )


def get_default_iptc_preset() -> IPTCPreset:
    """Get the default empty IPTC preset."""
    return IPTCPreset(
        name="Default",
        data=IPTCData(),
        is_default=True,
    )


def apply_iptc_to_image(image_path: Path, iptc_data: IPTCData) -> bool:
    """
    Apply IPTC metadata to an image file.
    
    For JPEG and processed images: embed IPTC directly into the image.
    For RAW images: create XMP sidecar file with IPTC metadata.

    Args:
        image_path: Path to the image file
        iptc_data: IPTC data to apply

    Returns:
        True if successful, False otherwise
    """
    if _is_raw_image(image_path):
        return _apply_iptc_to_xmp(image_path, iptc_data)
    return _apply_iptc_embedded(image_path, iptc_data)


def _is_raw_image(image_path: Path) -> bool:
    """Check if image is a RAW format."""
    raw_suffixes = {".cr2", ".cr3", ".nef", ".arw", ".raf", ".orf", ".rw2", ".dng", ".pef", ".srw"}
    return image_path.suffix.lower() in raw_suffixes


def _apply_iptc_embedded(image_path: Path, iptc_data: IPTCData) -> bool:
    """
    Apply IPTC metadata directly to image file (JPEG, PNG, TIFF, etc.)
    """
    try:
        import pyexiv2

        metadata = pyexiv2.ImageMetadata(str(image_path))
        metadata.read()

        # Set IPTC data
        if iptc_data.creator:
            metadata["Iptc.Application2.Writer"] = [iptc_data.creator]
        if iptc_data.copyright:
            metadata["Iptc.Application2.Copyright"] = [iptc_data.copyright]
        if iptc_data.credit:
            metadata["Iptc.Application2.Credit"] = [iptc_data.credit]
        if iptc_data.source:
            metadata["Iptc.Application2.Source"] = [iptc_data.source]
        if iptc_data.keywords:
            metadata["Iptc.Application2.Keywords"] = iptc_data.keywords

        metadata.write()
        return True
    except Exception:
        return False


def _apply_iptc_to_xmp(image_path: Path, iptc_data: IPTCData) -> bool:
    """
    Apply IPTC metadata to XMP sidecar file for RAW images.
    Creates or updates the .xmp file with IPTC data.
    """
    try:
        xmp_path = image_path.with_suffix(".xmp")

        # Build XMP content with IPTC data
        xmp_content = _build_iptc_xmp(iptc_data)

        if xmp_path.exists():
            # Merge with existing XMP
            with open(xmp_path, "r", encoding="utf-8") as f:
                existing_xmp = f.read()
            merged_xmp = _merge_iptc_into_xmp(existing_xmp, iptc_data)
            with open(xmp_path, "w", encoding="utf-8") as f:
                f.write(merged_xmp)
        else:
            # Create new XMP sidecar
            with open(xmp_path, "w", encoding="utf-8") as f:
                f.write(xmp_content)

        return True
    except Exception:
        return False


def _build_iptc_xmp(iptc_data: IPTCData) -> str:
    """Build XMP XML content with IPTC metadata."""
    # Build keywords XML
    keywords_xml = ""
    if iptc_data.keywords:
        keywords_xml = "\n    <dc:subject>\n     <rdf:Bag>"
        for kw in iptc_data.keywords:
            keywords_xml += f"\n      <rdf:li>{kw}</rdf:li>"
        keywords_xml += "\n     </rdf:Bag>\n    </dc:subject>"

    # Build creator XML
    creator_xml = ""
    if iptc_data.creator:
        creator_xml = f"\n    <dc:creator>\n     <rdf:Seq>\n      <rdf:li>{iptc_data.creator}</rdf:li>\n     </rdf:Seq>\n    </dc:creator>"

    # Build rights/copyright XML
    rights_xml = ""
    if iptc_data.copyright:
        rights_xml = f'\n    <dc:rights>{iptc_data.copyright}</dc:rights>'

    # Build photoshop XML for credit and source
    photoshop_xml = ""
    if iptc_data.credit:
        photoshop_xml += f'\n    <photoshop:Credit>{iptc_data.credit}</photoshop:Credit>'
    if iptc_data.source:
        photoshop_xml += f'\n    <photoshop:Source>{iptc_data.source}</photoshop:Source>'

    xmp_template = '''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 5.4.0">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/">{keywords}{creator}{rights}{photoshop}
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>'''

    return xmp_template.format(
        keywords=keywords_xml,
        creator=creator_xml,
        rights=rights_xml,
        photoshop=photoshop_xml
    )


def _merge_iptc_into_xmp(existing_xmp: str, iptc_data: IPTCData) -> str:
    """Merge IPTC data into existing XMP content."""
    # Simple approach: replace or add IPTC-related fields
    import re

    # Helper to replace or add a tag
    def replace_or_add(xmp: str, tag_pattern: str, new_tag: str) -> str:
        if re.search(tag_pattern, xmp):
            return re.sub(tag_pattern, new_tag, xmp)
        else:
            # Add before closing rdf:Description
            return xmp.replace("</rdf:Description>", new_tag + "\n  </rdf:Description>")

    # Update creator
    if iptc_data.creator:
        creator_tag = f"""    <dc:creator>
     <rdf:Seq>
      <rdf:li>{iptc_data.creator}</rdf:li>
     </rdf:Seq>
    </dc:creator>"""
        existing_xmp = replace_or_add(existing_xmp, r'<dc:creator>.*?</dc:creator>', creator_tag)

    # Update copyright/rights
    if iptc_data.copyright:
        rights_tag = f'    <dc:rights>{iptc_data.copyright}</dc:rights>'
        existing_xmp = replace_or_add(existing_xmp, r'<dc:rights>.*?</dc:rights>', rights_tag)

    # Update credit
    if iptc_data.credit:
        credit_tag = f'    <photoshop:Credit>{iptc_data.credit}</photoshop:Credit>'
        existing_xmp = replace_or_add(existing_xmp, r'<photoshop:Credit>.*?</photoshop:Credit>', credit_tag)

    # Update source
    if iptc_data.source:
        source_tag = f'    <photoshop:Source>{iptc_data.source}</photoshop:Source>'
        existing_xmp = replace_or_add(existing_xmp, r'<photoshop:Source>.*?</photoshop:Source>', source_tag)

    # Update keywords
    if iptc_data.keywords:
        keywords_xml = "    <dc:subject>\n     <rdf:Bag>"
        for kw in iptc_data.keywords:
            keywords_xml += f"\n      <rdf:li>{kw}</rdf:li>"
        keywords_xml += "\n     </rdf:Bag>\n    </dc:subject>"
        existing_xmp = replace_or_add(existing_xmp, r'<dc:subject>.*?</dc:subject>', keywords_xml)

    return existing_xmp


def read_iptc_from_image(image_path: Path) -> IPTCData:
    """
    Read IPTC metadata from an image file.
    
    For RAW images, tries to read from XMP sidecar first, then from embedded data.
    For other images, reads directly from the image file.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        IPTCData object with the read metadata
    """
    try:
        # For RAW images, try XMP sidecar first
        if _is_raw_image(image_path):
            xmp_path = image_path.with_suffix(".xmp")
            if xmp_path.exists():
                return _read_iptc_from_xmp(xmp_path)
        
        # Read from image directly
        return _read_iptc_embedded(image_path)
    except Exception:
        return IPTCData()


def _read_iptc_embedded(image_path: Path) -> IPTCData:
    """Read IPTC metadata directly from image file."""
    try:
        import pyexiv2
        
        metadata = pyexiv2.ImageMetadata(str(image_path))
        metadata.read()
        
        def get_first(metadata, key: str) -> str:
            """Get first value from metadata or empty string."""
            try:
                value = metadata.get(key, None)
                if value and hasattr(value, 'value') and value.value:
                    if isinstance(value.value, list):
                        return str(value.value[0]) if value.value else ""
                    return str(value.value)
                return ""
            except Exception:
                return ""
        
        def get_list(metadata, key: str) -> list[str]:
            """Get list value from metadata."""
            try:
                value = metadata.get(key, None)
                if value and hasattr(value, 'value') and value.value:
                    if isinstance(value.value, list):
                        return [str(v) for v in value.value]
                    return [str(value.value)]
                return []
            except Exception:
                return []
        
        return IPTCData(
            creator=get_first(metadata, "Iptc.Application2.Writer"),
            copyright=get_first(metadata, "Iptc.Application2.Copyright"),
            credit=get_first(metadata, "Iptc.Application2.Credit"),
            source=get_first(metadata, "Iptc.Application2.Source"),
            keywords=get_list(metadata, "Iptc.Application2.Keywords"),
        )
    except Exception:
        return IPTCData()


def _read_iptc_from_xmp(xmp_path: Path) -> IPTCData:
    """Read IPTC metadata from XMP sidecar file."""
    try:
        import xml.etree.ElementTree as ET
        import re
        
        with open(xmp_path, 'r', encoding='utf-8') as f:
            xmp_content = f.read()
        
        # Define namespaces
        namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
        }
        
        root = ET.fromstring(xmp_content)
        
        def get_text(xpath: str, ns: str = 'dc') -> str:
            """Extract text from XML element."""
            try:
                elem = root.find(xpath, namespaces)
                if elem is not None:
                    # Try to get text from rdf:li or direct text
                    li = elem.find('.//rdf:li', namespaces)
                    if li is not None and li.text:
                        return li.text
                    if elem.text:
                        return elem.text
                return ""
            except Exception:
                return ""
        
        def get_keywords() -> list[str]:
            """Extract keywords list."""
            try:
                subject = root.find('.//dc:subject', namespaces)
                if subject is not None:
                    bag = subject.find('.//rdf:Bag', namespaces)
                    if bag is not None:
                        return [li.text for li in bag.findall('rdf:li', namespaces) if li.text]
                return []
            except Exception:
                return []
        
        return IPTCData(
            creator=get_text('.//dc:creator'),
            copyright=get_text('.//dc:rights'),
            credit=get_text('.//photoshop:Credit', 'photoshop'),
            source=get_text('.//photoshop:Source', 'photoshop'),
            keywords=get_keywords(),
        )
    except Exception:
        return IPTCData()


def merge_iptc_data(
    existing: IPTCData, 
    new_data: IPTCData, 
    removed_keywords: set[str] = None,
    removed_fields: set[str] = None
) -> IPTCData:
    """
    Merge IPTC data, keeping existing values unless explicitly overridden or removed.
    
    Args:
        existing: Current IPTC data from image
        new_data: New IPTC data from UI
        removed_keywords: Set of keywords to remove (without asterisk)
        removed_fields: Set of field names to remove (creator, copyright, credit, source)
        
    Returns:
        Merged IPTCData
    """
    removed_fields = removed_fields or set()
    removed_keywords = removed_keywords or set()
    
    # For single-value fields:
    # - If field is in removed_fields -> clear it (empty string)
    # - If new_data has value -> use new value (override)
    # - Otherwise -> keep existing
    def merge_field(field_name: str, existing_val: str, new_val: str) -> str:
        if field_name in removed_fields:
            return ""  # User removed the asterisk-marked field
        if new_val:
            return new_val  # User entered new value
        return existing_val  # Keep existing
    
    merged = IPTCData(
        creator=merge_field("creator", existing.creator, new_data.creator),
        copyright=merge_field("copyright", existing.copyright, new_data.copyright),
        credit=merge_field("credit", existing.credit, new_data.credit),
        source=merge_field("source", existing.source, new_data.source),
        keywords=[],
    )
    
    # Merge keywords: keep existing (unless removed) + add new ones
    existing_keywords = set(existing.keywords)
    new_keywords = set(new_data.keywords)
    
    # Remove explicitly deleted keywords
    existing_keywords -= removed_keywords
    
    # Combine and sort
    merged_keywords = existing_keywords | new_keywords
    merged.keywords = sorted(list(merged_keywords))
    
    return merged
