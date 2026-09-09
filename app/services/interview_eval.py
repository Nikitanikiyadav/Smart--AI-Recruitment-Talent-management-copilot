"""
services/interview_eval.py
Heuristic scoring of a candidate's interview answer, plus adaptive
follow-up question selection and a final report generator.

IMPORTANT: This is a rule-based (keyword/length) scorer, not a real
language model judging semantic quality. It approximates useful signal
without needing a paid LLM API.
"""

import re
from typing import List, Optional, Dict
from app.schemas.interview import AnswerEvaluation, SkillCoverageItem, InterviewReport

SKILL_TERMS: Dict[str, List[str]] = {
    "python": ["function", "class", "list", "dictionary", "loop", "module", "package", "exception", "script"],
    "sql": ["query", "join", "index", "table", "select", "where", "primary key", "foreign key", "database"],
    "aws": ["ec2", "s3", "lambda", "cloud", "instance", "bucket", "iam", "deployment", "scaling"],
    "machine learning": ["model", "training", "dataset", "accuracy", "algorithm", "feature", "overfitting", "prediction"],
    "tensorflow": ["model", "layer", "tensor", "training", "neural network", "epoch", "gpu"],
    "docker": ["container", "image", "dockerfile", "volume", "deployment", "registry"],
    "git": ["commit", "branch", "merge", "repository", "pull request", "conflict"],
    "fastapi": ["endpoint", "route", "api", "request", "response", "async"],
    "react": ["component", "state", "props", "hook", "render", "jsx"],
    "kubernetes": ["pod", "cluster", "deployment", "container", "node", "service"],
}

FOLLOW_UP_DEEP = [
    "Can you go into more detail on how you measured the impact of that?",
    "What trade-offs did you consider before choosing that approach?",
    "How would that solution scale if the workload grew 10x?",
]

FOLLOW_UP_CLARIFY = [
    "Can you give a specific, concrete example from a real project?",
    "Let's slow down - can you walk me through that step by step?",
    "What tools or technologies did you specifically use there?",
]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def evaluate_answer(question: str, skill: Optional[str], answer_text: str) -> AnswerEvaluation:
    answer_text = (answer_text or "").strip()
    words = _word_count(answer_text)
    answer_lower = answer_text.lower()

    relevance = 3.0
    if skill and skill.lower() in answer_lower:
        relevance += 4.0
    if words >= 15:
        relevance += 2.0
    if words >= 40:
        relevance += 1.0
    relevance = min(10.0, relevance)

    terms = SKILL_TERMS.get((skill or "").lower(), [])
    if terms:
        hits = sum(1 for t in terms if t in answer_lower)
        accuracy = min(10.0, 3.0 + (hits / max(1, len(terms))) * 10)
    else:
        accuracy = min(10.0, 4.0 + (words / 20))

    if words < 10:
        completeness = 2.0
    elif words < 25:
        completeness = 5.0
    elif words < 60:
        completeness = 8.0
    else:
        completeness = 9.5

    overall = round((relevance * 0.4) + (accuracy * 0.35) + (completeness * 0.25), 1)
    relevance, accuracy, completeness = round(relevance, 1), round(accuracy, 1), round(completeness, 1)

    follow_up = None
    if overall >= 7.5:
        follow_up = FOLLOW_UP_DEEP[hash(question) % len(FOLLOW_UP_DEEP)]
    elif overall < 4.5:
        follow_up = FOLLOW_UP_CLARIFY[hash(question) % len(FOLLOW_UP_CLARIFY)]

    return AnswerEvaluation(
        relevance=relevance,
        technical_accuracy=accuracy,
        completeness=completeness,
        overall_score=overall,
        follow_up_question=follow_up,
    )


def build_report(candidate_name: Optional[str], job_title: str, results: List[dict]) -> InterviewReport:
    if not results:
        return InterviewReport(
            candidate_name=candidate_name,
            job_title=job_title,
            overall_score=0.0,
            recommendation="Insufficient Data",
            summary="No answers were recorded for this interview.",
            skill_coverage=[],
        )

    overall_avg = round(sum(r["overall_score"] for r in results) / len(results), 1)

    skill_scores: Dict[str, List[float]] = {}
    for r in results:
        skill = r.get("skill") or "General"
        skill_scores.setdefault(skill, []).append(r["overall_score"])

    coverage = []
    for skill, scores in skill_scores.items():
        avg = round(sum(scores) / len(scores), 1)
        if avg >= 7.5:
            status = "Strong"
        elif avg >= 5.0:
            status = "Adequate"
        else:
            status = "Needs Improvement"
        coverage.append(SkillCoverageItem(skill=skill, average_score=avg, status=status))

    coverage.sort(key=lambda c: c.average_score, reverse=True)

    if overall_avg >= 8.0:
        recommendation = "Strongly Recommend"
    elif overall_avg >= 6.0:
        recommendation = "Recommend"
    elif overall_avg >= 4.0:
        recommendation = "Consider with Reservations"
    else:
        recommendation = "Not Recommended"

    weak_skills = [c.skill for c in coverage if c.status == "Needs Improvement"]
    name = candidate_name or "The candidate"
    if weak_skills:
        weak_text = ", ".join(weak_skills)
        summary = f"{name} scored {overall_avg}/10 overall for the {job_title} role. Strong performance in most areas, but showed gaps in: {weak_text}."
    else:
        summary = f"{name} scored {overall_avg}/10 overall for the {job_title} role, with solid coverage across all assessed skills."

    return InterviewReport(
        candidate_name=candidate_name,
        job_title=job_title,
        overall_score=overall_avg,
        recommendation=recommendation,
        summary=summary,
        skill_coverage=coverage,
    )