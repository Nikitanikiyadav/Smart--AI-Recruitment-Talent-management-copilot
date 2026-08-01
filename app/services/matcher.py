"""
services/matcher.py
Core logic for scoring how well a candidate matches a job posting,
based on skill overlap (with a small bonus for meeting experience requirements).
"""

import re
from typing import List, Tuple, Optional


def _parse_skill_list(skills_str: str) -> List[str]:
    """Turn a comma-separated skills string into a clean list of skills."""
    if not skills_str:
        return []
    return [s.strip() for s in skills_str.split(",") if s.strip()]


def _extract_years_number(experience_str: Optional[str]) -> Optional[float]:
    """Pulls a numeric year value out of strings like '5 years'."""
    if not experience_str:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", experience_str)
    return float(match.group(1)) if match else None


def compute_match(
    candidate_skills: str,
    job_required_skills: str,
    candidate_experience_years: Optional[str] = None,
    job_min_experience_years: int = 0,
) -> Tuple[float, List[str], List[str]]:
    """
    Compare a candidate's skills against a job's required skills.

    Returns:
        (match_score 0-100, matched_skills, missing_skills)

    Scoring:
        - 90% weight: fraction of required skills the candidate has
        - 10% weight: whether the candidate meets the minimum experience requirement
    """
    candidate_list = _parse_skill_list(candidate_skills)
    required_list = _parse_skill_list(job_required_skills)

    candidate_lower = {s.lower() for s in candidate_list}

    matched = [s for s in required_list if s.lower() in candidate_lower]
    missing = [s for s in required_list if s.lower() not in candidate_lower]

    if not required_list:
        skill_score = 0.0
    else:
        skill_score = (len(matched) / len(required_list)) * 100

    experience_score = 100.0
    if job_min_experience_years and job_min_experience_years > 0:
        candidate_years = _extract_years_number(candidate_experience_years)
        if candidate_years is None:
            experience_score = 50.0
        elif candidate_years >= job_min_experience_years:
            experience_score = 100.0
        else:
            experience_score = max(0.0, (candidate_years / job_min_experience_years) * 100)

    final_score = round((skill_score * 0.9) + (experience_score * 0.1), 1)
    return final_score, matched, missing


def build_recommendation(candidate_name: Optional[str], missing_skills: List[str]) -> str:
    """Generate a short human-readable recommendation based on skill gaps."""
    name = candidate_name or "This candidate"
    if not missing_skills:
        return f"{name} meets all required skills for this role."
    if len(missing_skills) == 1:
        return f"{name} is missing {missing_skills[0]}. Consider targeted training or certification."
    skills_text = ", ".join(missing_skills[:-1]) + f" and {missing_skills[-1]}"
    return f"{name} has strong overlap but needs development in {skills_text}."