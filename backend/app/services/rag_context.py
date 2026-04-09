"""
RAG (Retrieval-Augmented Generation) context loader for Uzbek real estate terminology.

Loads the glossary JSON file and formats it for injection into the AI search
system prompt, providing GPT-4o-mini with domain-specific context for
parsing Uzbek-language property queries.
"""

import json
import logging
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger("propvision.services.rag_context")

GLOSSARY_PATH = Path(__file__).parent.parent / "data" / "uzbek_realestate_glossary.json"


@lru_cache()
def load_rag_context() -> str:
    """
    Load the Uzbek real estate glossary and format it as a string
    for injection into the AI search system prompt.

    The glossary is loaded once at startup and cached in memory.
    Returns a formatted string with terms, translations, and usage examples.
    """
    try:
        with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
            glossary = json.load(f)
    except FileNotFoundError:
        logger.warning(f"Glossary file not found at {GLOSSARY_PATH}")
        return "No glossary available."
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse glossary JSON: {e}")
        return "No glossary available."

    # Format glossary entries for the system prompt
    lines = []
    for category, terms in glossary.items():
        lines.append(f"\n## {category.upper()}")
        if isinstance(terms, list):
            for term in terms:
                if isinstance(term, dict):
                    uz = term.get("uz", "")
                    ru = term.get("ru", "")
                    en = term.get("en", "")
                    lines.append(f"- {uz} (RU: {ru}) = {en}")
                else:
                    lines.append(f"- {term}")
        elif isinstance(terms, dict):
            for key, value in terms.items():
                lines.append(f"- {key} = {value}")

    formatted = "\n".join(lines)
    logger.info(
        f"Loaded RAG context: {len(glossary)} categories, "
        f"{sum(len(v) if isinstance(v, list) else len(v.items()) for v in glossary.values())} terms"
    )
    return formatted
