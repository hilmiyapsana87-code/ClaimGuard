import re
from database import get_approved_facts


def normalize(text: str) -> str:
    text = text.casefold().strip()
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(".!? ")


# Matches quantities such as 10 grams, 30 g, 250 ml, or 5%
MEASUREMENT_PATTERN = re.compile(
    r"(?<!\w)(\d+(?:\.\d+)?)\s*"
    r"(grams?|g|mg|kg|milliliters?|ml|liters?|l|percent|%)"
    r"(?!\w)",
    re.IGNORECASE,
)


def extract_number_and_unit(text: str):
    match = MEASUREMENT_PATTERN.search(text)

    if not match:
        return None

    number = float(match.group(1))
    unit = match.group(2).casefold()

    unit_map = {
        "gram": "g",
        "grams": "g",
        "g": "g",
        "mg": "mg",
        "kg": "kg",
        "milliliter": "ml",
        "milliliters": "ml",
        "ml": "ml",
        "liter": "l",
        "liters": "l",
        "l": "l",
        "percent": "%",
        "%": "%",
    }

    return number, unit_map.get(unit, unit)


def remove_measurement(text: str) -> str:
    text = MEASUREMENT_PATTERN.sub("<measurement>", text.casefold())
    return normalize(text)


def verify_claim(claim: str, company_name: str) -> dict:
    claim = claim.strip()
    company_name = company_name.strip()

    if not claim or not company_name:
        return {
            "status": "UNVERIFIABLE",
            "reason": "A claim and company name are required.",
            "evidence": [],
        }

    facts = get_approved_facts(company_name)

    if not facts:
        return {
            "status": "UNVERIFIABLE",
            "reason": "No approved facts are available for this company.",
            "evidence": [],
        }

    # First, check for an exact match.
    for fact in facts:
        if normalize(claim) == normalize(fact["fact_text"]):
            return {
                "status": "SUPPORTED",
                "reason": "The claim exactly matches an approved fact.",
                "evidence": [fact],
            }

    # Next, check for a numerical conflict with otherwise identical wording.
    claim_measurement = extract_number_and_unit(claim)

    if claim_measurement:
        claim_without_measurement = remove_measurement(claim)

        for fact in facts:
            fact_measurement = extract_number_and_unit(fact["fact_text"])

            if not fact_measurement:
                continue

            fact_without_measurement = remove_measurement(
                fact["fact_text"]
            )

            # Define the comparison variables before using them.
            same_wording = (
                claim_without_measurement == fact_without_measurement
            )
            same_unit = claim_measurement[1] == fact_measurement[1]
            different_value = claim_measurement[0] != fact_measurement[0]

            if same_wording and same_unit and different_value:
                claim_value, claim_unit = claim_measurement
                fact_value, fact_unit = fact_measurement

                reason = (
                    f"Numerical conflict detected: the proposed claim "
                    f"states {claim_value:g} {claim_unit}, but the "
                    f"approved fact states {fact_value:g} {fact_unit}. "
                    f"The difference is "
                    f"{abs(claim_value - fact_value):g} {claim_unit}."
                )

                return {
                    "status": "CONTRADICTED",
                    "reason": reason,
                    "evidence": [fact],
                }

    return {
        "status": "UNVERIFIABLE",
        "reason": (
            "No sufficiently clear match or numerical contradiction "
            "was found in the approved facts."
        ),
        "evidence": [],
    }