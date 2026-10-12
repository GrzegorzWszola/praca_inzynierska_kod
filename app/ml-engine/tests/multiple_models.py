import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
MODEL_DIR = "./saved_models/all-MiniLM-L6-v2"
# MODEL_DIR = "./saved_models/all-mpnet-base-v2"
# MODEL_DIR = "./saved_models/BAAI/bge-base-en-v1.5"

profiler = Profiler()
metrics = Metrics()

configs = [PreMadeConfigs.mean_baseline(), PreMadeConfigs.median_baseline(), PreMadeConfigs.ridge(), PreMadeConfigs.xgboost(), PreMadeConfigs.xgboost_tree()]

# ----------- PREPARE SENTENCE TRANSFORMER -----------
sentence_transformer = True
if os.path.exists(MODEL_DIR):
    # Read locally installed model
    st_model = SentenceTransformer(MODEL_DIR)
else:
    # Save model after first start
    st_model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    st_model.save(MODEL_DIR)

# ----------- READ DATA -----------
train, dev, test = read_cr4(DATASET_CR4)
# train, dev, test = read_emo_bank(DATASET)
lexicon = read_lexicon(LEXICON)

# ----------- CREATE INPUTS -----------
if sentence_transformer:
    with profiler.measure("Sentence Transformer"):
        x_train = create_x_input_with_sentence_transformer(train["text"], st_model)
        x_dev = create_x_input_with_sentence_transformer(dev["text"], st_model)
else:
    with profiler.measure("Lexicon Transformation"):
        x_train = create_x_input_with_lexicon(train["text"], lexicon)
        x_dev = create_x_input_with_lexicon(dev["text"], lexicon)

y_train = train[['BERT_V', 'A', 'D']].to_numpy()
y_dev = dev[['BERT_V', 'A', 'D']].to_numpy()

for config in configs:
    # ----------- CREATE MODELS -----------
    try:
        ml_engine = MlEngine(config)
    except (ValueError, TypeError) as e:
        print(f"Error while creating model: {e}")
        exit(1)

    print(f"Current config: {ml_engine.model_name}")

    # ----------- TRAINING -----------
    with profiler.measure("Model Training", ml_engine.model_name):
        ml_engine.fit(x_train, y_train)

    # ----------- PREDICTION -----------
    with profiler.measure("Model Prediction", ml_engine.model_name):
        y_pred = ml_engine.model.predict(x_dev)

    metrics.compute_metrics(ml_engine.model_name, y_dev, y_pred)

metrics_report = metrics.report()
profiler_report = profiler.report()

save_raport_to_file("/home/grzeg/inz/app/ml-engine/tests/reports", metrics_report=metrics_report, profiling_report=profiler_report)



