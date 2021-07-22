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

csv_source = "data/documents_to_sentences_labeled-09-04-2020.csv"

def print_p(string = ""):
    print("{:.<80}".format(string), end = '')
    sys.stdout.flush()

print_p(f"Loading {csv_source}")
df = pd.read_csv(csv_source)
print("Done")

## Encode NaN Classes
df['target_class'] = df['target_class'].fillna("none")

## Encode to numeric classes
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(df['target_class'])

## Sampling data
print_p("Sampling data for training")
X_train, X_test, y_train, y_test = train_test_split(df[['sentence']], y_encoded, test_size = .3)
print("Done")

## Pipeline
print_p("Setting up Pipeline")
steps = [
    ('vectorizer', CountVectorizer()),
    # ('model', LogisticRegressionCV(max_iter = 2000, multi_class = 'ovr', cv = 3))
    # ('model', SGDClassifier(loss = 'log'))
    # ('model', RandomForestClassifier())
    ('model', MLPClassifier()) 
]
pipe = Pipeline(steps = steps)
print("Done")

print_p("Training model (this may take a while)")
## Fit model on core dataset with no sampling
start_time = time.time()
pipe_model = pipe.fit(df['sentence'], y_encoded)
print(f'Done in {time.time() - start_time} seconds')

print('Overall model score:', pipe_model.score(df['sentence'], y_encoded))
print('Detailed model performance by class:')

# Predicted classes
y_hat       = pipe_model.predict(df['sentence'])
y_hat_train = pipe_model.predict(X_train['sentence'])         ## Don't forget to train on this dataset as well
y_hat_test  = pipe_model.predict(X_test['sentence'])

# Predicted class probabilities
datasets = [
    dict(
        name                = "original",
        y                   = y_encoded,
        y_hat               = pipe_model.predict(df['sentence']),
        y_hat_probabilities = pipe_model.predict_proba(df['sentence'])
    ),
    dict(
        name                = "train",
        y                   = y_train,
        y_hat               = pipe_model.predict(X_train['sentence']),
        y_hat_probabilities = pipe_model.predict_proba(X_train['sentence'])
    ),
    dict(
        name                = "test",
        y                   = y_test,
        y_hat               = pipe_model.predict(X_test['sentence']),
        y_hat_probabilities = pipe_model.predict_proba(X_test['sentence'])
    ),
]

# Basic reports
get_reports = lambda: \
    {
        data['name']: classification_report(
            data['y'], 
            data['y_hat'],
            target_names = encoder.classes_
        ) for index, data in enumerate(datasets)
    }
reports = get_reports()

print("Original Data\n--------------------------------------------------------\n", reports['original'], "\n\n")
print("Train Data\n--------------------------------------------------------\n", reports['train'], "\n\n")
print("Test Data\n--------------------------------------------------------\n", reports['test'], "\n\n")

# save model
print_p("Saving model: model/sentence_model.joblib")
dump(pipe_model, "models/sentence_model.joblib")
dump(encoder, "models/sentence_label_encoder.joblib")
print("Done!")