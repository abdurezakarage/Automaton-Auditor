"""
VisionInspector tooling: extract images from PDFs and run multimodal (vision) analysis.

Used by the VisionInspector detective node to analyze diagrams and figures in the report PDF.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from langchain_core.messages import HumanMessage  # type: ignore[import]


@dataclass
class ExtractedImage:
    """A single image extracted from a PDF page."""

    page: int
    index_on_page: int
    image_bytes: bytes
    ext: str  # e.g. "png", "jpeg"


def extract_images_from_pdf(pdf_path: str) -> List[ExtractedImage]:
    """
    Extract all embedded images from a PDF using PyMuPDF.

    Returns a list of ExtractedImage (page, index, bytes, ext) for each image found.
    """
    try:
        import fitz  # type: ignore[import]
    except ImportError:
        return []

    path = Path(pdf_path)
    if not path.exists():
        return []

    result: List[ExtractedImage] = []
    try:
        doc = fitz.open(str(path))
        try:
            for page_index in range(len(doc)):
                page = doc[page_index]
                image_list = page.get_images(full=True)
                for img_index, img_ref in enumerate(image_list):
                    xref = img_ref[0]
                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        ext = base_image.get("ext", "png")
                        result.append(
                            ExtractedImage(
                                page=page_index + 1,
                                index_on_page=img_index,
                                image_bytes=image_bytes,
                                ext=ext,
                            )
                        )
                    except Exception:
                        continue
        finally:
            doc.close()
    except Exception:
        pass
    return result


def _image_to_data_url(img: ExtractedImage) -> str:
    """Encode image bytes as a data URL for vision API."""
    b64 = base64.standard_b64encode(img.image_bytes).decode("ascii")
    mime = "image/png" if img.ext.lower() == "png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


def analyze_images_with_vision(
    images: List[ExtractedImage],
    prompt: str,
    max_images: int = 8,
) -> str:
    """
    Run a vision-capable LLM over the extracted images and return analysis text.

    Uses the project's LLM (OpenAI/OpenRouter) with a vision-capable model to describe
    or analyze diagrams (e.g. architecture, flow, fan-out/fan-in).
    """
    if not images:
        return "No images extracted from PDF."

    from ..utils.llm_setup import get_llm

    try:
        llm = get_llm()
    except RuntimeError:
        return "Vision LLM not configured (missing API key). Cannot analyze images."

    # Limit number of images to avoid token limits and cost
    selected = images[:max_images]
    content: List[dict] = [{"type": "text", "text": prompt}]
    for img in selected:
        data_url = _image_to_data_url(img)
        content.append({
            "type": "image_url",
            "image_url": {"url": data_url},
        })

    msg = HumanMessage(content=content)
    try:
        response = llm.invoke([msg])
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        return f"Vision analysis failed: {e}"
