"""
Canonical knowledge base + synthetic training-data generator.

The recommender works on a 10-dimensional profile vector:

    aptitude : logical, analytical, verbal
    interests: science, technology, business, arts, healthcare, engineering, social

Each value is on a 0-100 scale.

`CAREER_PROFILES` is the single source of truth. It is used to:
  1. Seed the `Career` table (so the DB and the model never disagree).
  2. Generate a synthetic, labelled dataset to train the scikit-learn model.
  3. Provide the "ideal vector" used for cosine-similarity matching.

`PROGRAMS` defines university degree programs and which careers they serve.
"""
import numpy as np
import pandas as pd

# Feature order is fixed and shared everywhere.
FEATURES = [
    "logical", "analytical", "verbal",
    "science", "technology", "business",
    "arts", "healthcare", "engineering", "social",
]

INTEREST_AREAS = ["science", "technology", "business", "arts", "healthcare", "engineering", "social"]

# ---------------------------------------------------------------------------
# Careers — name -> metadata + ideal profile (0-100 on every feature)
# ---------------------------------------------------------------------------
CAREER_PROFILES = {
    "Software Engineer": {
        "icon": "bi-code-slash",
        "avg_salary": "$70k - $140k",
        "growth_outlook": "Very High",
        "description": "Designs, builds and maintains software systems and applications.",
        "profile": {"logical": 92, "analytical": 85, "verbal": 55, "science": 50,
                     "technology": 95, "business": 45, "arts": 35, "healthcare": 10,
                     "engineering": 65, "social": 35},
    },
    "Data Scientist": {
        "icon": "bi-graph-up",
        "avg_salary": "$80k - $150k",
        "growth_outlook": "Very High",
        "description": "Turns large datasets into insight using statistics and machine learning.",
        "profile": {"logical": 88, "analytical": 95, "verbal": 60, "science": 80,
                     "technology": 88, "business": 60, "arts": 25, "healthcare": 20,
                     "engineering": 55, "social": 30},
    },
    "Mechanical Engineer": {
        "icon": "bi-gear-wide-connected",
        "avg_salary": "$60k - $110k",
        "growth_outlook": "Steady",
        "description": "Designs and tests mechanical devices, engines and machines.",
        "profile": {"logical": 85, "analytical": 80, "verbal": 45, "science": 70,
                     "technology": 65, "business": 40, "arts": 30, "healthcare": 10,
                     "engineering": 95, "social": 25},
    },
    "Civil Engineer": {
        "icon": "bi-bricks",
        "avg_salary": "$58k - $105k",
        "growth_outlook": "Steady",
        "description": "Plans and supervises construction of infrastructure such as roads and buildings.",
        "profile": {"logical": 80, "analytical": 75, "verbal": 50, "science": 60,
                     "technology": 55, "business": 45, "arts": 40, "healthcare": 10,
                     "engineering": 92, "social": 35},
    },
    "Physician (Doctor)": {
        "icon": "bi-heart-pulse",
        "avg_salary": "$120k - $250k",
        "growth_outlook": "High",
        "description": "Diagnoses and treats illness, caring for patients' health and wellbeing.",
        "profile": {"logical": 70, "analytical": 85, "verbal": 65, "science": 92,
                     "technology": 45, "business": 30, "arts": 20, "healthcare": 97,
                     "engineering": 20, "social": 70},
    },
    "Registered Nurse": {
        "icon": "bi-clipboard2-pulse",
        "avg_salary": "$55k - $95k",
        "growth_outlook": "Very High",
        "description": "Provides hands-on patient care and supports doctors in clinical settings.",
        "profile": {"logical": 55, "analytical": 60, "verbal": 65, "science": 70,
                     "technology": 35, "business": 25, "arts": 25, "healthcare": 95,
                     "engineering": 10, "social": 85},
    },
    "Business Analyst": {
        "icon": "bi-bar-chart-line",
        "avg_salary": "$60k - $110k",
        "growth_outlook": "High",
        "description": "Bridges business needs and technical solutions through data and process analysis.",
        "profile": {"logical": 70, "analytical": 88, "verbal": 75, "science": 35,
                     "technology": 60, "business": 92, "arts": 30, "healthcare": 15,
                     "engineering": 30, "social": 55},
    },
    "Accountant / Financial Analyst": {
        "icon": "bi-cash-coin",
        "avg_salary": "$55k - $100k",
        "growth_outlook": "Steady",
        "description": "Manages financial records, budgets and investment analysis.",
        "profile": {"logical": 80, "analytical": 85, "verbal": 55, "science": 30,
                     "technology": 45, "business": 90, "arts": 15, "healthcare": 10,
                     "engineering": 25, "social": 40},
    },
    "Lawyer": {
        "icon": "bi-bank",
        "avg_salary": "$80k - $180k",
        "growth_outlook": "Steady",
        "description": "Advises and represents clients on legal matters and disputes.",
        "profile": {"logical": 78, "analytical": 80, "verbal": 95, "science": 25,
                     "technology": 35, "business": 65, "arts": 35, "healthcare": 10,
                     "engineering": 15, "social": 75},
    },
    "Psychologist": {
        "icon": "bi-people",
        "avg_salary": "$55k - $110k",
        "growth_outlook": "High",
        "description": "Studies behaviour and helps people manage mental and emotional challenges.",
        "profile": {"logical": 60, "analytical": 75, "verbal": 85, "science": 70,
                     "technology": 30, "business": 30, "arts": 40, "healthcare": 70,
                     "engineering": 10, "social": 92},
    },
    "Graphic / UX Designer": {
        "icon": "bi-palette",
        "avg_salary": "$45k - $95k",
        "growth_outlook": "High",
        "description": "Creates visual and interactive designs for products, brands and media.",
        "profile": {"logical": 50, "analytical": 55, "verbal": 60, "science": 20,
                     "technology": 65, "business": 45, "arts": 95, "healthcare": 10,
                     "engineering": 30, "social": 55},
    },
    "Architect": {
        "icon": "bi-building",
        "avg_salary": "$60k - $120k",
        "growth_outlook": "Steady",
        "description": "Designs buildings that balance aesthetics, function and safety.",
        "profile": {"logical": 70, "analytical": 70, "verbal": 55, "science": 50,
                     "technology": 55, "business": 45, "arts": 88, "healthcare": 10,
                     "engineering": 80, "social": 45},
    },
    "Journalist / Content Writer": {
        "icon": "bi-pencil-square",
        "avg_salary": "$40k - $85k",
        "growth_outlook": "Moderate",
        "description": "Researches, writes and communicates stories across media platforms.",
        "profile": {"logical": 55, "analytical": 60, "verbal": 95, "science": 30,
                     "technology": 45, "business": 45, "arts": 70, "healthcare": 10,
                     "engineering": 10, "social": 75},
    },
    "Teacher / Educator": {
        "icon": "bi-mortarboard",
        "avg_salary": "$42k - $80k",
        "growth_outlook": "Steady",
        "description": "Educates and mentors students, designing lessons and assessments.",
        "profile": {"logical": 60, "analytical": 60, "verbal": 85, "science": 45,
                     "technology": 40, "business": 30, "arts": 45, "healthcare": 20,
                     "engineering": 20, "social": 90},
    },
}

# ---------------------------------------------------------------------------
# University programs — each maps to one or more careers (by name).
# ---------------------------------------------------------------------------
PROGRAMS = [
    {"name": "BS Computer Science", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Core computing, algorithms, software development and systems.",
     "universities": "MIT, Stanford, NUST, FAST-NUCES, COMSATS",
     "careers": ["Software Engineer", "Data Scientist"]},
    {"name": "BS Software Engineering", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Engineering-focused study of large-scale software design and delivery.",
     "universities": "Carnegie Mellon, NUST, FAST-NUCES, UET",
     "careers": ["Software Engineer"]},
    {"name": "BS Data Science / Artificial Intelligence", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Statistics, machine learning, data engineering and AI systems.",
     "universities": "UC Berkeley, NUST, ITU, GIKI",
     "careers": ["Data Scientist", "Software Engineer"]},
    {"name": "BS Mechanical Engineering", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Mechanics, thermodynamics, design and manufacturing.",
     "universities": "Georgia Tech, UET, NUST, GIKI",
     "careers": ["Mechanical Engineer"]},
    {"name": "BS Civil Engineering", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Structures, transportation, geotechnical and environmental engineering.",
     "universities": "UET, NUST, MUET, Purdue",
     "careers": ["Civil Engineer", "Architect"]},
    {"name": "MBBS (Bachelor of Medicine)", "degree_level": "Bachelor", "duration": "5 years",
     "description": "Comprehensive medical education leading to clinical practice.",
     "universities": "Harvard Medical, Aga Khan University, King Edward Medical, Dow",
     "careers": ["Physician (Doctor)"]},
    {"name": "BS Nursing", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Clinical nursing care, patient management and health sciences.",
     "universities": "Johns Hopkins, Aga Khan University, Dow University",
     "careers": ["Registered Nurse"]},
    {"name": "BBA (Business Administration)", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Management, marketing, finance and organisational behaviour.",
     "universities": "Wharton, LUMS, IBA, NUST Business School",
     "careers": ["Business Analyst", "Accountant / Financial Analyst"]},
    {"name": "BS Accounting & Finance", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Financial accounting, auditing, taxation and investment analysis.",
     "universities": "LSE, LUMS, IBA, SZABIST",
     "careers": ["Accountant / Financial Analyst", "Business Analyst"]},
    {"name": "LLB (Bachelor of Laws)", "degree_level": "Bachelor", "duration": "5 years",
     "description": "Constitutional, civil, criminal and corporate law.",
     "universities": "Harvard Law, Punjab University Law College, LUMS",
     "careers": ["Lawyer"]},
    {"name": "BS Psychology", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Human behaviour, cognition, clinical and counselling psychology.",
     "universities": "Stanford, GC University, FCCU, Bahria",
     "careers": ["Psychologist"]},
    {"name": "BS / BFA Graphic & UX Design", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Visual communication, interaction design and digital media.",
     "universities": "RISD, NCA, Indus Valley, BNU",
     "careers": ["Graphic / UX Designer"]},
    {"name": "B.Arch (Architecture)", "degree_level": "Bachelor", "duration": "5 years",
     "description": "Architectural design, structures and urban planning.",
     "universities": "NCA, UET, NED, Cornell",
     "careers": ["Architect"]},
    {"name": "BS Media Studies / Journalism", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Reporting, content production, communication and media ethics.",
     "universities": "Columbia Journalism, FCCU, Punjab University, Bahria",
     "careers": ["Journalist / Content Writer"]},
    {"name": "BS / B.Ed Education", "degree_level": "Bachelor", "duration": "4 years",
     "description": "Pedagogy, curriculum design and educational psychology.",
     "universities": "Teachers College Columbia, AIOU, IER Punjab University",
     "careers": ["Teacher / Educator"]},
]


def career_vector(name: str) -> np.ndarray:
    """Return the ideal feature vector (length 10) for a career name."""
    profile = CAREER_PROFILES[name]["profile"]
    return np.array([profile[f] for f in FEATURES], dtype=float)


def generate_synthetic_dataset(samples_per_career: int = 220, seed: int = 42) -> pd.DataFrame:
    """
    Build a labelled dataset by sampling noisy profiles around each career's
    ideal vector. This gives the scikit-learn classifier realistic, separable
    yet overlapping data to learn from.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for name in CAREER_PROFILES:
        ideal = career_vector(name)
        for _ in range(samples_per_career):
            # Gaussian noise + occasional larger perturbation for realism.
            noise = rng.normal(0, 11, size=ideal.shape)
            jitter = rng.normal(0, 4, size=ideal.shape)
            sample = np.clip(ideal + noise + jitter, 0, 100)
            row = dict(zip(FEATURES, sample))
            row["career"] = name
            rows.append(row)
    return pd.DataFrame(rows)


