from ml_engine.metrics import Metrics
from ml_engine.engine import MlEngine
from ml_engine.config import PreMadeConfigs
from ml_engine.profiler import Profiler
from sentence_transformers import SentenceTransformer
import os
from test_utils import read_emo_bank, read_lexicon, create_x_input_with_lexicon, read_cr4, create_x_input_with_sentence_transformer, save_raport_to_file

DATASET_CR4 = "/home/grzeg/inz/app/ml-engine/tests/data/cr4_narr_dataset.csv"
DATASET = "/home/grzeg/inz/app/ml-engine/tests/data/main_dataset.csv"
LEXICON = "/home/grzeg/inz/app/ml-engine/tests/data/nrc_vad_lexicon_dataset.csv"
# MODEL_DIR = "./saved_models/all-MiniLM-L6-v2"
MODEL_DIR = "./saved_models/all-mpnet-base-v2"

profiler = Profiler()
metrics = Metrics()

# ----------- PREPARE SENTENCE TRANSFORMER -----------
sentence_transformer = True
if os.path.exists(MODEL_DIR):
    # Read locally installed model
    st_model = SentenceTransformer(MODEL_DIR)
else:
    # Save model after first start
    st_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    st_model.save(MODEL_DIR)

# ----------- CREATE MODELS -----------
try:
    config = PreMadeConfigs.ridge()
    ml_engine = MlEngine(config)
except (ValueError, TypeError) as e:
    print(f"Error while creating model: {e}")
    exit(1)

# ----------- READ DATA -----------
train, dev, test = read_cr4(DATASET_CR4)
lexicon = read_lexicon(LEXICON)

# ----------- CREATE INPUTS -----------
if sentence_transformer:
    with profiler.measure(ml_engine.model_name, "Sentence Transformer"):
        x_train = create_x_input_with_sentence_transformer(train["text"], st_model)
        x_dev = create_x_input_with_sentence_transformer(dev["text"], st_model)
else:
    with profiler.measure(ml_engine.model_name, "Lexicon Transformation"):
        x_train = create_x_input_with_lexicon(train["text"], lexicon)
        x_dev = create_x_input_with_lexicon(dev["text"], lexicon)

# ----------- TRAINING -----------
with profiler.measure(ml_engine.model_name, "Model Training"):
    y_train = train[['BERT_V', 'A', 'D']].to_numpy()
    ml_engine.fit(x_train, y_train)

# ----------- PREDICTION -----------
with profiler.measure(ml_engine.model_name, "Model Prediction"):
    y_dev = dev[['BERT_V', 'A', 'D']].to_numpy()
    y_pred = ml_engine.model.predict(x_dev)

metrics.compute_metrics(ml_engine.model_name, y_dev, y_pred)

metrics_report = metrics.report()
profiler_report = profiler.report()

save_raport_to_file("/home/grzeg/inz/app/ml-engine/tests/reports", metrics_report=metrics_report, profiling_report=profiler_report)
