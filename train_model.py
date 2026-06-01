"""Train the AI career-recommendation model and save it to disk.

Run:  python train_model.py

This is optional — the app will lazily train the model on first use if the
saved model file is missing — but running it ahead of time makes the first
recommendation instant.
"""
from config import Config
from app.ml.recommender import train_and_save


def main():
    print("Training career recommendation model...")
    info = train_and_save(Config.MODEL_PATH, verbose=True)
    print("-" * 50)
    print(f"  Samples trained on : {info['n_samples']}")
    print(f"  Careers (classes)  : {info['n_careers']}")
    print(f"  Holdout accuracy   : {info['accuracy']:.3f}")
    print(f"  Model saved to     : {Config.MODEL_PATH}")
    print("Done.")


if __name__ == "__main__":
    main()


