import csv
from collections import defaultdict

TSV = "mtg-jamendo-dataset/data/autotagging.tsv"
MIN_DURATION = 60  # sekundy

EMOTIONS = {
    "joy":        {"happy", "uplifting", "upbeat", "positive", "hopeful", "inspiring", "fun", "party", "epic", "action", "adventure"},
    "sadness":    {"sad", "melancholic", "emotional", "ballad"},
    "tense":      {"dark", "horror", "dramatic", "soundscape", "powerful", "heavy", "aggressive"},
    "calm":       {"calm", "relaxing", "meditative", "soft", "mellow", "slow", "dream"},
    "neutral":    {"background", "documentary", "nature", "film", "melodic"},
}

# gatunki, które nie pasują do łagodnej muzyki np. do książek fantasy
BAD_GENRES = {
    "electronic", "electronica", "edm", "techno", "house", "deephouse", "trance",
    "dubstep", "drumnbass", "breakbeat", "eurodance", "dance", "club", "disco",
    "hiphop", "rap", "metal", "hard", "grunge",
    "industrial", "synthpop", "electropop", "idm", "reggae", "latin", "funk",
}
# nastroje wykluczające (imprezowe, reklamowe, świąteczne...)
BAD_MOODS = {"party", "sexy", "funny", "christmas", "holiday", "children",
             "sport", "commercial", "advertising", "groovy", "fast", "retro"}

def read_tracks(path):
    with open(path, encoding="utf-8") as f:
        next(f)  # nagłówek
        for line in f:
            p = line.rstrip("\n").split("\t")
            tags = {"genre": set(), "mood/theme": set(), "instrument": set()}
            for t in p[5:]:
                cat, name = t.split("---")
                tags[cat].add(name)
            yield {"id": p[0], "path": p[3], "duration": float(p[4]), **tags}

raw = defaultdict(int)       # same tagi nastroju
filtered = defaultdict(int)  # po odfiltrowaniu gatunków/nastrojów/czasu
selected = defaultdict(list)

for tr in read_tracks(TSV):
    ok = (
        tr["duration"] >= MIN_DURATION
        and not (tr["genre"] & BAD_GENRES)
        and not (tr["mood/theme"] & BAD_MOODS)
    )
    for emo, moods in EMOTIONS.items():
        if tr["mood/theme"] & moods:
            raw[emo] += 1
            if ok:
                filtered[emo] += 1
                selected[emo].append(tr)

print(f"{'emocja':10} {'surowo':>8} {'po filtrach':>12}")
for emo in EMOTIONS:
    print(f"{emo:10} {raw[emo]:>8} {filtered[emo]:>12}")
