## Data related
import pandas as pd, numpy as np

## Data Visualization
import matplotlib.pyplot as plt
from cycler import cycler

## Sampling and feature encoding
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import LabelBinarizer, LabelEncoder

## Modeling
from sklearn.linear_model import LogisticRegressionCV, SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

## Evaluation
from sklearn.metrics import classification_report
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
import time, sys

## Model persistance
from joblib import dump, load

model_file   = "models/sentence_model.joblib"
encoder_file = "models/sentence_label_encoder.joblib"
print(f"Loading model {model_file}..")
pipe_model   = load(model_file)
encoder      = load(encoder_file)

sentence = input("Enter a sentence to classify: ")
prediction = pipe_model.predict([sentence])
probas = pipe_model.predict_proba([sentence])
print(f"Predicted class: {encoder.classes_[prediction[0]]}")
print("Class probabilities:")
class_probas = {class_name: probas[0][index].round(4) for index, class_name in enumerate(encoder.classes_)}
print(class_probas)