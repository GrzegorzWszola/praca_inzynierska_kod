from pathlib import Path

from ml_engine.lexicon import lookup
from sklearn.model_selection import train_test_split
import datetime as dt
import pandas as pd
import numpy as np

def read_emo_bank(dataset):
    df = pd.read_csv(dataset)
    df = df.dropna(subset=['text'])
    train = df[df['split'] == "train"]
    dev = df[df['split'] == "dev"]
    test = df[df['split'] == "test"]
    return train, dev, test

def read_cr4(dataset):
    cols = ['text', 'BERT_V', 'A', 'D']
    data = pd.read_csv(dataset, usecols=cols)
    data = data.dropna(subset=cols)
    train, temp = train_test_split(data, test_size=0.3, random_state=42)
    dev, test = train_test_split(temp, test_size=0.5, random_state=42)
    return train, dev, test

def read_lexicon(LEXICON):
    lexicon_df = pd.read_csv(LEXICON)
    return {
        row.term: (row.V, row.A, row.D)
        for row in lexicon_df.itertuples()
    }

def create_x_input_with_lexicon(data_set, lexicon):
    x = []
    for sentence in data_set:
        mean_arr = lookup(sentence, lexicon)
        x.append(mean_arr)
    return np.array(x)

def create_x_input_with_sentence_transformer(data_set, model):
    return model.encode(data_set.tolist())

def save_raport_to_file(file_path, metrics_report=None, profiling_report=None):
    timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_path = Path(file_path)
    base_path.mkdir(parents=True, exist_ok=True)

    if metrics_report:
        metrics_path = base_path / f"metrics_{timestamp}.csv"
        with open(metrics_path, "w", encoding="utf-8") as f:
            headers = list(dict.fromkeys(k for r in metrics_report for k in r.keys()))
            f.write(";".join(headers) + "\n")
            for report in metrics_report:
                row = [str(report.get(k, "")) for k in headers]
                f.write(";".join(row) + "\n")

    if profiling_report:
        profiling_path = base_path / f"profiling_{timestamp}.csv"
        with open(profiling_path, "w", encoding="utf-8") as f:
            headers = list(dict.fromkeys(k for r in profiling_report for k in r.keys()))
            f.write(";".join(headers) + "\n")
            for report in profiling_report:
                row = [
                    str(round(report.get(k), 4)) if isinstance(report.get(k), float) else str(report.get(k, ""))
                    for k in headers
                ]
                f.write(";".join(row) + "\n")


