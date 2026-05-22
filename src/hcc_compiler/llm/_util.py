from __future__ import annotations
import re

# Matches a JSON object anywhere in an LLM response (greedy, dot-all via [\s\S]).
_JSON_RE = re.compile(r"\{[\s\S]*\}")
