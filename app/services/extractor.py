"""
services/extractor.py
Uses spaCy NLP + regex heuristics to pull structured fields
(name, email, phone, education, experience, skills, location)
out of raw resume text.
"""

import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[\s-]?)?\(?\d{3,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}")
EXPERIENCE_REGEX = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience", re.IGNORECASE)

EDUCATION_KEYWORDS = [
    "B.Tech", "M.Tech", "B.E", "M.E", "MBA", "BCA", "MCA", "B.Sc", "M.Sc",
    "Bachelor", "Master", "PhD", "Ph.D", "MS Computer Science", "MS ",
    "Computer Science", "Information Technology", "Diploma"
]

SKILLS_DB = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "SQL", "NoSQL",
    "FastAPI", "Django", "Flask", "React", "Angular", "Vue", "Node.js",
    "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch",
    "Data Analysis", "Data Science", "Pandas", "NumPy", "Scikit-learn",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "CI/CD",
    "MySQL", "PostgreSQL", "MongoDB", "SQLite", "REST API", "GraphQL",
    "Project Management", "Agile", "Scrum", "Excel", "Power BI", "Tableau",
    "HTML", "CSS", "Spring Boot", "Linux",
]


def extract_email(text: str) -> str | None:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = PHONE_REGEX.search(text)
    return match.group(0).strip() if match else None


def extract_experience(text: str) -> str | None:
    match = EXPERIENCE_REGEX.search(text)
    if match:
        return f"{match.group(1)} years"
    return None


def extract_education(text: str) -> str | None:
    for keyword in EDUCATION_KEYWORDS:
        if keyword.lower() in text.lower():
            for line in text.splitlines():
                if keyword.lower() in line.lower():
                    return line.strip()
    return None


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = [skill for skill in SKILLS_DB if skill.lower() in text_lower]
    return sorted(set(found))


def _looks_like_a_name(line: str) -> bool:
    """Heuristic check: does this line look like 'First Last' rather than a heading/skill?"""
    line = line.strip()
    if not line or len(line) > 40:
        return False
    if "@" in line or any(ch.isdigit() for ch in line):
        return False
    words = [w for w in line.split() if w]
    if not (1 < len(words) <= 4):
        return False
    lowered = line.lower()
    banned = ["resume", "curriculum vitae", "cv", "profile", "summary", "contact"]
    if any(b in lowered for b in banned):
        return False
    if any(skill.lower() == lowered for skill in SKILLS_DB):
        return False
    for w in words:
        if w.isalpha() and not w[0].isupper():
            return False
    return True


def extract_name_and_location(text: str) -> tuple[str | None, str | None]:
    """Guess the candidate's name and location.
    Name: prefer the resume's first non-empty line if it looks like a name,
    otherwise fall back to spaCy's PERSON entity.
    Location: use spaCy's GPE entity, filtered against known skills.
    """
    name = None
    location = None

    for line in text.splitlines():
        if _looks_like_a_name(line):
            name = line.strip()
            break

    if nlp is None:
        return name, location

    doc = nlp(text[:1000])
    skill_words_lower = {s.lower() for s in SKILLS_DB}

    for ent in doc.ents:
        if ent.label_ == "PERSON" and name is None:
            candidate = ent.text.strip()
            if candidate.lower() not in skill_words_lower:
                name = candidate
        if ent.label_ == "GPE" and location is None:
            candidate = ent.text.strip()
            if candidate.lower() not in skill_words_lower:
                location = candidate
        if name and location:
            break

    return name, location


def extract_fields(text: str) -> dict:
    """Run all extractors and return a structured candidate profile dict."""
    name, location = extract_name_and_location(text)

    profile = {
        "name": name,
        "email": extract_email(text),
        "phone": extract_phone(text),
        "location": location,
        "education": extract_education(text),
        "experience_years": extract_experience(text),
        "skills": ", ".join(extract_skills(text)),
    }
    return profile