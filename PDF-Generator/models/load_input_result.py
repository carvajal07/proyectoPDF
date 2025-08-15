from dataclasses import dataclass
from xml.etree.ElementTree import Element
from typing import Any, Dict, List

@dataclass
class LoadInputResult:
    layout: Element
    full_context: Dict[str, Any]
    documents: List[Dict[str, Any]]
    config_dicts: Dict[str, Dict]
    data_dicts: Dict[str, Dict]
    grouped_nodes: Dict[str, List]
    all_elements: Dict[str, Any]
    parastyle_reportlabs: Dict[str, Any]
    fonts_reportlabs: Dict[str, Any]
    colors_reportlabs: Dict[str, Any]
    borderstyle_reportlabs: Dict[str, Any]
    images_cache: Dict[str, Any]
