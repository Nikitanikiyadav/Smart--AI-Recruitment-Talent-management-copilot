"""
services/interview_gen.py
Generates role-specific interview questions from a job posting's required
skills, using templated question banks per category. This is a rule-based
generator (not a live LLM call), so it works offline with no API costs.
"""

import random
from typing import List, Optional
from app.schemas.interview import InterviewQuestion

TECHNICAL_TEMPLATES = [
    ("Describe a project where you used {skill}. What challenges did you face and how did you solve them?", "3-5 min response"),
    ("How would you explain {skill} to someone with little technical background?", "2-3 min response"),
    ("What best practices do you follow when working with {skill}?", "3-4 min response"),
]

SCENARIO_TEMPLATES = [
    ("Imagine you're deploying a solution that relies on {skill} into production. What considerations would you take into account?", "4-6 min response"),
    ("If you found a critical bug involving {skill} right before a release, how would you handle it?", "3-5 min response"),
]

BEHAVIORAL_TEMPLATES = [
    ("Tell me about a time you had to explain a complex {skill}-related concept to a non-technical stakeholder. How did you ensure they understood?", "2-4 min response"),
    ("Describe a situation where you disagreed with a teammate about how to approach a {skill} problem. How did you resolve it?", "3-4 min response"),
]

EXPERIENCE_TEMPLATES = [
    ("Walk me through your experience working with {skill} across different projects.", "4-5 min response"),
    ("What's the most challenging {skill} problem you've solved, and what was your approach?", "3-5 min response"),
]

CATEGORY_MAP = {
    "Technical Skills": ("Technical", TECHNICAL_TEMPLATES),
    "Scenario-based": ("Scenario-based", SCENARIO_TEMPLATES),
    "Behavioral": ("Behavioral", BEHAVIORAL_TEMPLATES),
    "Experience-based": ("Experience-based", EXPERIENCE_TEMPLATES),
}

GENERIC_OPENERS = [
    ("Tell me a little about yourself and what draws you to this role.", "Behavioral", "2-3 min response"),
    ("Why are you interested in this position?", "Behavioral", "2-3 min response"),
]


def _parse_skills(skills_str: str) -> List[str]:
    if not skills_str:
        return []
    return [s.strip() for s in skills_str.split(",") if s.strip()]


def generate_questions(
    job_title: str,
    required_skills: str,
    category_filter: Optional[str] = None,
    max_questions: int = 6,
) -> List[InterviewQuestion]:
    """
    Build a list of interview questions for a job posting.
    If category_filter is given (e.g. "Technical Skills"), only that category
    of question is generated (one per required skill, up to max_questions).
    Otherwise, a mixed set across all categories is returned.
    """
    skills = _parse_skills(required_skills)
    if not skills:
        skills = [job_title]  # fallback so we still produce something

    questions: List[InterviewQuestion] = []

    if category_filter and category_filter in CATEGORY_MAP:
        label, templates = CATEGORY_MAP[category_filter]
        for skill in skills:
            if len(questions) >= max_questions:
                break
            template, resp_time = random.choice(templates)
            questions.append(InterviewQuestion(
                question=template.format(skill=skill),
                category=label,
                skill=skill,
                suggested_response_time=resp_time,
            ))
    else:
        # Mixed set: one opener, then rotate through categories per skill
        opener_q, opener_cat, opener_time = random.choice(GENERIC_OPENERS)
        questions.append(InterviewQuestion(
            question=opener_q, category=opener_cat, skill=None,
            suggested_response_time=opener_time,
        ))
        categories = list(CATEGORY_MAP.values())
        for i, skill in enumerate(skills):
            if len(questions) >= max_questions:
                break
            label, templates = categories[i % len(categories)]
            template, resp_time = random.choice(templates)
            questions.append(InterviewQuestion(
                question=template.format(skill=skill),
                category=label,
                skill=skill,
                suggested_response_time=resp_time,
            ))

    return questions[:max_questions]