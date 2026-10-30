import csv
import io

from fastapi import HTTPException
from pydantic import ValidationError

from app.features.candidates.schema import CandidateCreate

COLUMNS = list(CandidateCreate.model_fields)


def parse_candidates(content: str) -> list[CandidateCreate]:
    reader = csv.DictReader(io.StringIO(content))
    missing = [column for column in COLUMNS if column not in (reader.fieldnames or [])]
    if missing:
        raise HTTPException(400, f"Missing columns: {', '.join(missing)}")

    candidates = []
    for number, row in enumerate(reader, start=2):
        try:
            candidates.append(CandidateCreate(**{c: (row[c] or "").strip() for c in COLUMNS}))
        except ValidationError:
            raise HTTPException(400, f"Row {number} is not valid")
    return candidates
