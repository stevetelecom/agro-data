"""Entraînement du modèle de détection de la pourriture brune.

Rôle : transfert d'apprentissage MobileNetV2 sur le jeu d'images de cabosses
(BF2). Le script est **optionnel** : il n'est pas exécuté par la CI, qui ne
dispose ni de TensorFlow ni du jeu d'images validé par le PO. Tant qu'il n'a
pas tourné, l'inférence reste en mode démonstration (`is_demo: true`).

Organisation attendue du jeu d'images :

    ai/dataset/
      train/
        sain/            *.jpg, *.jpeg, *.png
        pourriture/      *.jpg, *.jpeg, *.png
      validation/
        sain/
        pourriture/

Usage :

    python ai/train.py --dataset ai/dataset --epochs 15
    python ai/train.py --help

Dépendances (non installées par défaut, pour ne pas alourdir la CI) :

    pip install tensorflow

Auteur : MEKONTSO Olivier Steve (MOD-A5, issue #14).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
BASE_MODEL = "mobilenetv2"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "model" / "phytophthora_mobilenetv2.keras"
DEFAULT_METRICS_PATH = Path(__file__).resolve().parent / "model" / "metrics.json"
CLASSES = ("sain", "pourriture")


def _require_tensorflow():
    """Importe TensorFlow avec un message explicite s'il manque."""
    try:
        import tensorflow as tf  # noqa: F401
    except ImportError as exc:  # pragma: no cover - dépend de l'environnement
        raise SystemExit(
            "TensorFlow est requis pour l'entraînement : pip install tensorflow"
        ) from exc
    return tf


def build_model(tf):
    """Construit MobileNetV2 (ImageNet) + tête de classification binaire."""
    base = tf.keras.applications.MobileNetV2(
        input_shape=(*IMAGE_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=(*IMAGE_SIZE, 3))
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
    )
    return model


def load_datasets(tf, dataset_dir: Path):
    """Charge les dossiers `train/` et `validation/` avec un split 80/20 de secours."""
    train_dir = dataset_dir / "train"
    validation_dir = dataset_dir / "validation"
    if not train_dir.is_dir():
        raise SystemExit(f"Jeu d'images introuvable : {train_dir}")

    common = {
        "labels": "inferred",
        "label_mode": "binary",
        "class_names": list(CLASSES),
        "image_size": IMAGE_SIZE,
        "batch_size": BATCH_SIZE,
    }
    train_ds = tf.keras.utils.image_dataset_from_directory(train_dir, validation_split=0.2,
                                                           subset="training", seed=42, **common)
    if validation_dir.is_dir():
        validation_ds = tf.keras.utils.image_dataset_from_directory(validation_dir, **common)
    else:
        validation_ds = tf.keras.utils.image_dataset_from_directory(
            train_dir, validation_split=0.2, subset="validation", seed=42, **common
        )
    return train_ds, validation_ds


def main() -> int:
    parser = argparse.ArgumentParser(description="Entraînement MobileNetV2 AGRO-DATA")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).resolve().parent / "dataset")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--model-out", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--metrics-out", type=Path, default=DEFAULT_METRICS_PATH)
    args = parser.parse_args()

    tf = _require_tensorflow()
    train_ds, validation_ds = load_datasets(tf, args.dataset)

    model = build_model(tf)
    history = model.fit(train_ds, validation_data=validation_ds, epochs=args.epochs)

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    model.save(args.model_out)

    # Précision honnête : on rapporte la dernière époque de validation.
    metrics = {
        "base_model": BASE_MODEL,
        "image_size": list(IMAGE_SIZE),
        "epochs": args.epochs,
        "class_names": list(CLASSES),
        "val_accuracy": float(history.history.get("val_accuracy", [0.0])[-1]),
        "val_auc": float(history.history.get("val_auc", [0.0])[-1]),
        "model_path": str(args.model_out),
    }
    args.metrics_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
