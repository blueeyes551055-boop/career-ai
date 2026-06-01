"""
Aptitude-test scoring and answer validation.

Given the active questions and the raw answers submitted from the dashboard,
this module:
  * validates that every question is answered with a sensible value,
  * computes normalised (0-100) scores for each aptitude category,
  * computes a 0-100 score for each interest area,
  * returns a 10-feature profile dict ready for the recommender.

Invalid or missing input raises `InvalidTestSubmission`, which the route
turns into a friendly error message — the project must never produce career
advice from incomplete data.
"""
from .ml.dataset import INTEREST_AREAS

APTITUDE_CATEGORIES = ["logical_reasoning", "analytical_thinking", "verbal_ability"]

# Map aptitude category -> profile feature key.
_APT_FEATURE = {
    "logical_reasoning": "logical",
    "analytical_thinking": "analytical",
    "verbal_ability": "verbal",
}


class InvalidTestSubmission(Exception):
    """Raised when submitted answers are missing or malformed."""


def score_submission(questions, answers: dict):
    """
    Parameters
    ----------
    questions : list[Question]   active questions presented to the student
    answers   : dict             {str(question_id): value}
                                 mcq  -> option index (int / numeric string)
                                 likert -> 1..5

    Returns
    -------
    dict with keys:
        logical, analytical, verbal      (0-100)
        overall                          (0-100, mean of the three)
        interest                         {area: 0-100}
        profile                          full 10-feature dict for recommender
        category_breakdown               per-category correct/total
    """
    if not questions:
        raise InvalidTestSubmission("No active questions are available for the test.")
    if not isinstance(answers, dict) or not answers:
        raise InvalidTestSubmission("No answers were submitted. Please complete the test.")

    apt_correct = {c: 0 for c in APTITUDE_CATEGORIES}
    apt_total = {c: 0 for c in APTITUDE_CATEGORIES}
    interest_sum = {a: 0.0 for a in INTEREST_AREAS}
    interest_count = {a: 0 for a in INTEREST_AREAS}

    for q in questions:
        key = str(q.id)
        if key not in answers or answers[key] in (None, "", []):
            raise InvalidTestSubmission(
                "Please answer every question before submitting the test."
            )
        raw = answers[key]

        if q.qtype == "mcq":
            try:
                choice = int(raw)
            except (ValueError, TypeError):
                raise InvalidTestSubmission("One or more answers had an invalid format.")
            if choice < 0 or choice >= len(q.options):
                raise InvalidTestSubmission("An answer referred to an option that does not exist.")
            if q.category in apt_total:
                apt_total[q.category] += 1
                if q.correct_index is not None and choice == q.correct_index:
                    apt_correct[q.category] += 1

        elif q.qtype == "likert":
            try:
                value = int(raw)
            except (ValueError, TypeError):
                raise InvalidTestSubmission("One or more rating answers had an invalid format.")
            if value < 1 or value > 5:
                raise InvalidTestSubmission("Rating answers must be between 1 and 5.")
            area = q.interest_area
            if area in interest_sum:
                interest_sum[area] += value
                interest_count[area] += 1
        else:
            raise InvalidTestSubmission(f"Unknown question type: {q.qtype}")

    # --- aptitude scores (percentage correct) ----------------------------
    apt_scores = {}
    for c in APTITUDE_CATEGORIES:
        apt_scores[c] = round(100.0 * apt_correct[c] / apt_total[c], 1) if apt_total[c] else 0.0

    logical = apt_scores["logical_reasoning"]
    analytical = apt_scores["analytical_thinking"]
    verbal = apt_scores["verbal_ability"]
    overall = round((logical + analytical + verbal) / 3.0, 1)

    # --- interest scores (likert 1-5 mapped to 0-100) --------------------
    interest = {}
    for area in INTEREST_AREAS:
        if interest_count[area]:
            avg = interest_sum[area] / interest_count[area]    # 1..5
            interest[area] = round((avg - 1) / 4.0 * 100.0, 1)  # 0..100
        else:
            interest[area] = 0.0

    profile = {
        "logical": logical, "analytical": analytical, "verbal": verbal,
        **interest,
    }

    return {
        "logical": logical,
        "analytical": analytical,
        "verbal": verbal,
        "overall": overall,
        "interest": interest,
        "profile": profile,
        "category_breakdown": {
            c: {"correct": apt_correct[c], "total": apt_total[c]} for c in APTITUDE_CATEGORIES
        },
    }


