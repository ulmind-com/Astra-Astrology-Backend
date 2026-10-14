"""Beanie document registry.

Add each new model class here and it gets registered (with its indexes) on
startup. Empty for now — no collections are defined yet.
"""

from beanie import Document

DOCUMENT_MODELS: list[type[Document]] = []

__all__ = ["DOCUMENT_MODELS"]
