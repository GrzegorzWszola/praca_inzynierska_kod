from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()
reader_csv = os.getenv("EMO_BANK_READER")
emobank_csv = os.getenv("EMO_BANK_BASE")
output_path = os.getenv("OUTPUT_EMO_BANK")

lexicon_file_path = os.getenv("LEXICON_FILE")
lexicon_output_file_path = os.getenv("LEXICON_OUTPUT")

cr4nar_csv = os.getenv("CR4_NARR_FILE")
cr4nar_output = os.getenv("OUTPUT_CR4_NARR")

def transform():
    if not reader_csv or not emobank_csv or not output_path:
        raise ValueError("Error while loading files")

    df_reader = pd.read_csv(reader_csv, usecols=["id", "V", "A", "D", "stdV", "stdA", "stdD", "N"])
    df_emobank = pd.read_csv(emobank_csv, usecols=["id", "split", "text"])
    print(f"[Emo Bank] File read and dataframe created: {lexicon_file_path}")

    df = pd.merge(df_emobank, df_reader, on="id", how="inner")
    df[["V", "A", "D"]] = ((df[["V", "A", "D"]] - 3) * 0.5).round(4)
    df[["stdV", "stdA", "stdD"]] = (df[["stdV", "stdA", "stdD"]] * 0.5).round(4)
    print(f"[Emo Bank] Save to: {output_path}")
    df.to_csv(output_path, index=False)

def transform_nrc_vad_lexicon():
    df = pd.read_csv(lexicon_file_path, sep='\t')
    print(f"[Lexicon] File read and dataframe created: {lexicon_file_path}")
    df = df.rename(columns={
        "valence": "V",
        "arousal": "A",
        "dominance": "D"
    })
    print(f"[Lexicon] File created and data transformed, saved to: {lexicon_output_file_path}")
    df.to_csv(lexicon_output_file_path, index=False)

def transform_cr4narremote():
    df = pd.read_csv(
        cr4nar_csv,
        usecols=["file_id", "user_id", "subject_ids", "passage",
                 "t1_corrected", "NRC_valence", "NRC_arousal",
                 "NRC_dominance", "NRCBERT_valence"],
    )
    print(f"[Cr4Narr] File read and dataframe created: {cr4nar_csv}")

    numeric_cols = ["NRC_valence", "NRC_arousal", "NRC_dominance", "NRCBERT_valence"]

    agg_step1 = {c: "mean" for c in numeric_cols}
    agg_step1["passage"] = "first"
    df = df.groupby(["subject_ids", "user_id"]).agg(agg_step1).reset_index()

    agg_step2 = {c: "mean" for c in numeric_cols}
    agg_step2["passage"] = "first"
    df = df.groupby("subject_ids").agg(agg_step2).reset_index()

    df[numeric_cols] = (df[numeric_cols] * 2 - 1).round(4)

    df = df.rename(columns={
        "NRC_valence": "V", 
        "NRC_arousal": "A", 
        "NRC_dominance": "D", 
        "NRCBERT_valence": "BERT_V",
        "passage": "text",
        "subject_ids": "text_id"
    })
    print(f"[Cr4Narr] File created and data transformed, saved to: {cr4nar_output}")
    df.to_csv(cr4nar_output, index=False)

if __name__ == "__main__":
    transform()
    transform_nrc_vad_lexicon()
    transform_cr4narremote()