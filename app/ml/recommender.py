"""
Career recommendation engine.

Approach (hybrid, interpretable + learned):
  1. A scikit-learn Pipeline  (StandardScaler -> RandomForestClassifier) is
     trained on a synthetic dataset built from the career knowledge base.
     It outputs a probability for every career given a student's profile.
  2. Cosine similarity between the student's profile and each career's ideal
     vector gives an interpretable "fit" signal.
  3. The two signals are blended into a final match score (0-100) and the top
     careers are returned, each with a short, human-readable explanation.

Blending the learned model with similarity makes results both accurate and
explainable, and keeps the system working even before the model is trained.
"""
import os
import numpy as np
import joblib

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from .dataset import (
    FEATURES, INTEREST_AREAS, CAREER_PROFILES,
    career_vector, generate_synthetic_dataset,
)

# Weight given to the learned classifier vs. cosine similarity.
MODEL_WEIGHT = 0.6
SIM_WEIGHT = 0.4

# Friendly labels for explanations.
_LABELS = {
    "logical": "logical reasoning", "analytical": "analytical thinking",
    "verbal": "verbal ability", "science": "science interest",
    "technology": "technology interest", "business": "business interest",
    "arts": "creative / arts interest", "healthcare": "healthcare interest",
    "engineering": "engineering interest", "social": "people / social interest",
}


def profile_to_vector(profile: dict) -> np.ndarray:
    """Convert a {feature: score} dict to an ordered numpy vector."""
    return np.array([float(profile.get(f, 0)) for f in FEATURES], dtype=float)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_and_save(model_path: str, verbose: bool = True) -> dict:
    """Train the classifier on synthetic data and persist it to `model_path`."""
    df = generate_synthetic_dataset()
    X = df[FEATURES].values
    y = df["career"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=250, max_depth=None, min_samples_leaf=2,
            random_state=42, n_jobs=-1)),
    ])
    pipeline.fit(X_train, y_train)

    acc = accuracy_score(y_test, pipeline.predict(X_test))

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump({"pipeline": pipeline, "classes": list(pipeline.classes_)}, model_path)

    if verbose:
        print(f"[recommender] trained on {len(X_train)} samples, "
              f"held-out accuracy = {acc:.3f}")
        print(f"[recommender] model saved to {model_path}")

    return {"accuracy": acc, "n_samples": len(df), "n_careers": len(pipeline.classes_)}


# ---------------------------------------------------------------------------
# Recommender (singleton-style loader)
# ---------------------------------------------------------------------------
class CareerRecommender:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._bundle = None

    def _ensure_model(self):
        """Load the model, training it on first use if necessary."""
        if self._bundle is not None:
            return
        if not os.path.exists(self.model_path):
            train_and_save(self.model_path, verbose=False)
        self._bundle = joblib.load(self.model_path)

    def _classifier_scores(self, vector: np.ndarray) -> dict:
        self._ensure_model()
        pipe = self._bundle["pipeline"]
        classes = self._bundle["classes"]
        proba = pipe.predict_proba(vector.reshape(1, -1))[0]
        return dict(zip(classes, proba))

    def _explanation(self, vector: np.ndarray, career_name: str) -> str:
        """Pick the student's two strongest features that the career also values."""
        ideal = career_vector(career_name)
        # Importance = how much this career relies on a feature AND how well
        # the student scores there.
        contributions = [(f, ideal[i] * vector[i]) for i, f in enumerate(FEATURES)]
        contributions.sort(key=lambda x: x[1], reverse=True)
        top = [_LABELS[f] for f, _ in contributions[:2]]
        return f"Strong match with your {top[0]} and {top[1]}."

    def recommend(self, profile: dict, top_n: int = 4):
        """
        Return a ranked list of career recommendations.

        Each item: {name, match (0-100), description, icon, avg_salary,
                    growth_outlook, reason}
        """
        vector = profile_to_vector(profile)

        clf_scores = self._classifier_scores(vector)
        # Normalise classifier probabilities to 0..1 (already are) and combine
        # with cosine similarity to each career's ideal vector.
        results = []
        for name, meta in CAREER_PROFILES.items():
            sim = _cosine(vector, career_vector(name))           # 0..1
            clf = float(clf_scores.get(name, 0.0))                # 0..1
            blended = MODEL_WEIGHT * clf + SIM_WEIGHT * sim
            results.append((name, blended, clf, sim, meta))

        results.sort(key=lambda r: r[1], reverse=True)

        # Scale the blended scores into a friendly 0-100 "match" percentage.
        top = results[:top_n]
        max_blend = max((r[1] for r in top), default=1.0) or 1.0
        recommendations = []
        for name, blended, clf, sim, meta in top:
            # Map to a 55-99 range so the best option never looks weak,
            # while preserving the relative ordering.
            match = round(55 + (blended / max_blend) * 44, 1)
            recommendations.append({
                "name": name,
                "match": match,
                "description": meta["description"],
                "icon": meta["icon"],
                "avg_salary": meta["avg_salary"],
                "growth_outlook": meta["growth_outlook"],
                "reason": self._explanation(vector, name),
            })
        return recommendations


