from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()
reader_csv = os.getenv("EMO_BANK_READER")
emobank_csv = os.getenv("EMO_BANK_BASE")
output_path = os.getenv("OUTPUT_EMO_BANK")

lexicon_file_path = os.getenv("LEXICON_FILE")
lexicon_output_file_path = os.getenv("LEXICON_OUTPUT")

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

if __name__ == "__main__":
    transform()
    transform_nrc_vad_lexicon()