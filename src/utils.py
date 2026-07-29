import logging
import os
import re
from data import MODEL_TO_NAME_MAPPING, LIMIT_LABELS_ID

MISSING_MODELS = set()

def create_logger(provider_name):
    logger = logging.getLogger(provider_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(f"{provider_name}: %(message)s")
    handler.setFormatter(formatter)
    # avoid adding multiple handlers if already exists
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

def get_model_name(id):
    id = id.lower()
    if id in MODEL_TO_NAME_MAPPING:
        return MODEL_TO_NAME_MAPPING[id]
    MISSING_MODELS.add(id)
    return id

def env_ready(*keys):
    """True jika semua env key terisi."""
    return all(os.environ.get(k) for k in keys)

def get_human_limits(model, seperator="<br>"):
    if not model or "limits" not in model:
        return ""
    limits = model["limits"]
    # filter None values
    limits = {key: value for key, value in limits.items() if value is not None}
    parts = []
    for key, value in limits.items():
        label = LIMIT_LABELS_ID.get(key, key)
        if isinstance(value, (int, float)):
            parts.append(f"{value:,} {label}".replace(",", "."))
        else:
            parts.append(f"{value} {label}")
    return seperator.join(parts)

def provider_meta(jenis="gratis", batas=None, catatan=None):
    """Blok meta singkat di bawah judul provider (tampil konsisten)."""
    lines = [f"> **Jenis:** {jenis}"]
    if batas:
        lines.append(f"> **Batas:** {batas}")
    if catatan:
        lines.append(f"> **Catatan:** {catatan}")
    return "\n".join(lines) + "\n\n"

def generate_toc(markdown):
    toc_lines = []
    # Find all ## and ### headings, but skip the main title (# ...)
    headings = re.findall(r"^(#{2,3}) +(.+)", markdown, re.MULTILINE)
    for hashes, title in headings:
        # Remove markdown links for anchor text, keep display text
        display = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", title)
        # Build anchor (GitHub style)
        anchor = display.lower()
        anchor = re.sub(r"[^a-z0-9 \-_]", "", anchor)
        anchor = anchor.replace(" ", "-")
        anchor = anchor.replace("--", "-")
        anchor = anchor.strip("-")
        indent = "  " if len(hashes) == 3 else ""
        toc_lines.append(f"{indent}- [{display}](#{anchor})")
    return "\n".join(toc_lines)
