from pathlib import Path
import tarfile
import shutil

# BEFORE DOWNLOAD MUSIC FROM JTGJAMENDO

TSV = "mtg-jamendo-dataset/data/autotagging.tsv"
TAR_DIR = "/home/grzeg/inz/data/mtg-jamendo-dataset/download"
OUTPUT_DIR = "/home/grzeg/inz/data/sorted_moods"
LOW_QUALITY = True

MIN_DURATION = 60

EMOTIONS = {
    "joy":     {"happy", "uplifting", "upbeat", "positive", "hopeful", "inspiring", "fun", "party", "epic", "action", "adventure"},
    "sadness": {"sad", "melancholic", "emotional", "ballad"},
    "tense":   {"dark", "horror", "dramatic", "soundscape", "powerful", "heavy", "aggressive"},
    "calm":    {"calm", "relaxing", "meditative", "soft", "mellow", "slow", "dream"},
    "neutral": {"background", "documentary", "nature", "film", "melodic"},
}

BAD_GENRES = {
    "electronic", "electronica", "edm", "techno", "house", "deephouse", "trance",
    "dubstep", "drumnbass", "breakbeat", "eurodance", "dance", "club", "disco",
    "hiphop", "rap", "metal", "hard", "grunge",
    "industrial", "synthpop", "electropop", "idm", "reggae", "latin", "funk",
}

BAD_MOODS = {"party", "sexy", "funny", "christmas", "holiday", "children",
             "sport", "commercial", "advertising", "groovy", "fast", "retro"}


def load_filtered_tracks(path):
    """Reads tsv and returns dict of filepath emotion_label"""
    target_tracks = {}

    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 6:
                continue

            audio_rel_path = p[3]
            if LOW_QUALITY:
                audio_rel_path = p[3].split('.')[0] + ".low.mp3"

            try:
                duration = float(p[4])
            except ValueError:
                continue

            tags = {"genre": set(), "mood/theme": set(), "instrument": set()}
            for t in p[5:]:
                if "---" in t:
                    cat, name = t.split("---", 1)
                    if cat in tags:
                        tags[cat].add(name)

            ok = (
                duration >= MIN_DURATION
                and not (tags["genre"] & BAD_GENRES)
                and not (tags["mood/theme"] & BAD_MOODS)
            )
            if not ok:
                continue

            assigned = {emo for emo, moods in EMOTIONS.items()
                        if tags["mood/theme"] & moods}

            if len(assigned) == 1:
                target_tracks[audio_rel_path] = next(iter(assigned))

    return target_tracks


def extract_selected(tar_path, final_path, tracks):
    """Unpacks only set items and saves into proper folder"""
    count = 0
    try:
        with tarfile.open(tar_path, "r") as tar:
            for member in tar:
                if not member.isfile():
                    continue

                name = member.name.removeprefix("./")
                emo = tracks.get(name)
                if emo is None:
                    continue

                dest_dir = final_path / emo
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / Path(name).name
                if dest_file.exists():
                    continue

                src = tar.extractfile(member)
                if src is None:
                    continue
                with src, open(dest_file, "wb") as out:
                    shutil.copyfileobj(src, out)
                count += 1
    except (tarfile.TarError, OSError) as e:
        print(f"Error with {tar_path.name}: {e}")
    return count


if __name__ == "__main__":
    filtered_tracks = load_filtered_tracks(TSV)
    print(f"Picked {len(filtered_tracks)} tracks")

    tar_dir = Path(TAR_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    tar_files = sorted(tar_dir.glob("*.tar"))
    if not tar_files:
        print("Empty catalog")
        exit(1)

    total = 0
    for tar_path in tar_files:
        n = extract_selected(tar_path, out_dir, filtered_tracks)
        total += n
        print(f"{tar_path.name}: {n} tracks")

    print(f"Finished, finally {total} tracks")
    for emo in EMOTIONS:
        d = out_dir / emo
        if d.exists():
            print(f"  {emo}: {len(list(d.glob('*.mp3')))}")