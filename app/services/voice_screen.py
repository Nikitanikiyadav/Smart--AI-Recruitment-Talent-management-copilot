"""
services/voice_screen.py
Generates a short "preliminary assessment" from a voice-screening transcript.
Heuristic (keyword/length-based), not a real LLM judging the transcript -
same honest approach as the interview answer evaluator.
"""

import re
from typing import List, Optional


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def assess_transcript(transcript: str, job_title: str, required_skills: str) -> dict:
    """
    Produce a short preliminary assessment paragraph plus a recommended next step,
    based on transcript length and how many of the job's required skills were
    actually mentioned during the screening call.
    """
    transcript = (transcript or "").strip()
    words = _word_count(transcript)
    transcript_lower = transcript.lower()

    skills = [s.strip() for s in (required_skills or "").split(",") if s.strip()]
    mentioned = [s for s in skills if s.lower() in transcript_lower]

    if words < 15:
        return {
            "assessment": "The recording was too short to draw a meaningful assessment. Consider re-running the screening with more open-ended prompts.",
            "recommended_next_step": "Re-screen",
            "skills_mentioned": mentioned,
        }

    coverage_ratio = len(mentioned) / len(skills) if skills else 0.0

    if coverage_ratio >= 0.6 and words >= 25:
        assessment = (
            f"Candidate demonstrates clear communication and touched on "
            f"{len(mentioned)} of {len(skills)} required skills for the {job_title} role "
            f"({', '.join(mentioned) if mentioned else 'general experience'}). "
            f"Recommended for a full technical interview round."
        )
        next_step = "Advance to Technical Interview"
    elif coverage_ratio >= 0.3 or words >= 60:
        assessment = (
            f"Candidate communicated reasonably well but only referenced "
            f"{len(mentioned)} of {len(skills)} required skills. Worth a follow-up "
            f"screening call to probe specific technical experience for {job_title}."
        )
        next_step = "Follow-up Screening"
    else:
        assessment = (
            f"Limited relevant technical content detected in this screening call for "
            f"the {job_title} role. Consider whether this candidate's background "
            f"aligns with the required skill set before proceeding."
        )
        next_step = "Review Fit"

    return {
        "assessment": assessment,
        "recommended_next_step": next_step,
        "skills_mentioned": mentioned,
    }