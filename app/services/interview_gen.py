"""
services/interview_gen.py
Generates role-specific interview questions from a job posting's required
skills, tailored to the candidate's resume (resume-aware) and the job
description (JD-aware). Rule-based / templated generator - no external
LLM API call, so it works offline with no API costs.
"""

import random
from typing import List, Optional
from app.schemas.interview import InterviewQuestion

TECHNICAL_TEMPLATES = [
    ("Describe a project where you used {skill}. What challenges did you face and how did you solve them?", "3-5 min response"),
    ("How would you explain {skill} to someone with little technical background?", "2-3 min response"),
    ("What best practices do you follow when working with {skill}?", "3-4 min response"),
]

TECHNICAL_TEMPLATES_ADVANCED = [
    ("You've listed {skill} on your resume - walk me through the most complex thing you've built with it.", "4-6 min response"),
    ("What's a mistake you made early on with {skill} that changed how you use it today?", "3-5 min response"),
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

GROWTH_AREA_TEMPLATES = [
    ("This role requires {skill}, which isn't listed on your resume. What's your familiarity with it, if any?", "2-3 min response"),
    ("How would you go about ramping up on {skill} if you started this role tomorrow?", "2-3 min response"),
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


def get_difficulty(min_experience_years: int) -> str:
    if not min_experience_years or min_experience_years < 2:
        return "Beginner"
    if min_experience_years < 5:
        return "Intermediate"
    return "Advanced"


def _jd_snippet(description: Optional[str]) -> Optional[str]:
    if not description:
        return None
    sentences = [s.strip() for s in description.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return None
    return sentences[0][:140]


def generate_questions(
    job_title: str,
    required_skills: str,
    description: Optional[str] = None,
    candidate_skills: Optional[str] = None,
    category_filter: Optional[str] = None,
    max_questions: int = 6,
) -> List[InterviewQuestion]:
    skills = _parse_skills(required_skills)
    if not skills:
        skills = [job_title]

    candidate_skill_set = {s.strip().lower() for s in _parse_skills(candidate_skills or "")}

    questions: List[InterviewQuestion] = []

    if category_filter and category_filter in CATEGORY_MAP:
        label, templates = CATEGORY_MAP[category_filter]
        for skill in skills:
            if len(questions) >= max_questions:
                break
            has_skill = skill.lower() in candidate_skill_set
            if category_filter == "Technical Skills" and has_skill:
                template, resp_time = random.choice(TECHNICAL_TEMPLATES_ADVANCED)
            else:
                template, resp_time = random.choice(templates)
            questions.append(InterviewQuestion(
                question=template.format(skill=skill),
                category=label,
                skill=skill,
                suggested_response_time=resp_time,
                resume_match=has_skill,
            ))
    else:
        opener_q, opener_cat, opener_time = random.choice(GENERIC_OPENERS)
        questions.append(InterviewQuestion(
            question=opener_q, category=opener_cat, skill=None,
            suggested_response_time=opener_time, resume_match=None,
        ))

        categories = list(CATEGORY_MAP.values())
        for i, skill in enumerate(skills):
            if len(questions) >= max_questions:
                break
            has_skill = skill.lower() in candidate_skill_set

            if candidate_skills and not has_skill and random.random() < 0.5:
                template, resp_time = random.choice(GROWTH_AREA_TEMPLATES)
                label = "Growth Area"
            else:
                label, templates = categories[i % len(categories)]
                if label == "Technical" and has_skill:
                    template, resp_time = random.choice(TECHNICAL_TEMPLATES_ADVANCED)
                else:
                    template, resp_time = random.choice(templates)

            questions.append(InterviewQuestion(
                question=template.format(skill=skill),
                category=label,
                skill=skill,
                suggested_response_time=resp_time,
                resume_match=has_skill,
            ))

        jd_phrase = _jd_snippet(description)
        if jd_phrase and len(questions) >= 2:
            questions[-1] = InterviewQuestion(
                question=f"The role description mentions: \"{jd_phrase}\". Can you share relevant experience related to that?",
                category="Experience-based",
                skill=questions[-1].skill,
                suggested_response_time="3-5 min response",
                resume_match=questions[-1].resume_match,
            )

    return questions[:max_questions]