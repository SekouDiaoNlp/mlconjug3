import json
import logging
from pathlib import Path
from collections import defaultdict

# =========================
# CONFIG
# =========================

INPUT_DIR = Path("./unimorph_data")
OUTPUT_DIR = Path("conjugation_data")
OUTPUT_DIR.mkdir(exist_ok=True)

LOG_FILE = "unimorph_parser.log"

# =========================
# LOGGING
# =========================

logger = logging.getLogger("unimorph")
logger.setLevel(logging.DEBUG)

fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setFormatter(fmt)
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setFormatter(fmt)
ch.setLevel(logging.INFO)

logger.addHandler(fh)
logger.addHandler(ch)

# =========================
# FEATURE HELPERS
# =========================

def parse_feats(s):
    return set(s.split(";"))

def is_verb(f):
    return "V" in f

def is_infinitive(f):
    return "INF" in f

# =========================
# SLOT MAPPING (CRITICAL)
# =========================

def get_slot(features):
    mood = None
    tense = None
    person = None

    if "IND" in features:
        mood = "Indicatif"
    elif "SBJV" in features:
        mood = "Subjonctif"
    elif "IMP" in features:
        mood = "Imperatif"
    elif "COND" in features:
        mood = "Conditionnel"

    if "PRS" in features:
        tense = "Présent"
    elif "PST" in features:
        tense = "Passé"
    elif "FUT" in features:
        tense = "Futur"
    elif "IPFV" in features or "IMPF" in features:
        tense = "Imparfait"

    if "1" in features:
        person = 0
    elif "2" in features:
        person = 1
    elif "3" in features:
        person = 2

    if "PL" in features and person is not None:
        person += 3

    if mood and tense and person is not None:
        return (mood, tense, person)

    return None

# =========================
# ROOT EXTRACTION
# =========================

def longest_common_prefix(strings):
    if not strings:
        return ""
    s1 = min(strings)
    s2 = max(strings)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1

def compute_root(infinitive, forms):
    return longest_common_prefix([infinitive] + forms)

# =========================
# MAIN PARSER
# =========================

def parse_language(lang_dir):
    lang = lang_dir.name
    file_path = lang_dir / lang

    if not file_path.exists():
        logger.warning(f"{lang}: missing main file")
        return

    logger.info(f"=== Processing {lang} ===")

    lemmas = defaultdict(list)

    # -------------------------
    # READ FILE
    # -------------------------
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, 1):
            parts = line.strip().split("\t")
            if len(parts) != 3:
                continue

            lemma, form, feat_str = parts
            feats = parse_feats(feat_str)

            if not is_verb(feats):
                continue

            lemmas[lemma].append((form, feats))

    logger.info(f"{lang}: {len(lemmas)} verb lemmas")

    # =========================
    # BUILD SIGNATURES
    # =========================

    signatures = {}
    lemma_data = {}

    for lemma, entries in lemmas.items():
        try:
            infinitives = [f for f, feat in entries if is_infinitive(feat)]
            infinitive = infinitives[0] if infinitives else lemma

            forms = [f for f, _ in entries]
            root = compute_root(infinitive, forms)

            slots = {}

            for form, feat in entries:
                slot = get_slot(feat)
                if slot is None:
                    continue

                ending = form[len(root):] if form.startswith(root) else form
                slots[slot] = ending

            if not slots:
                continue

            signature = tuple(sorted(slots.items()))

            signatures.setdefault(signature, []).append(infinitive)

            lemma_data[infinitive] = {
                "root": root,
                "slots": slots
            }

        except Exception as e:
            logger.debug(f"{lang}: error on {lemma}: {e}")

    logger.info(f"{lang}: {len(signatures)} conjugation classes")

    # =========================
    # ASSIGN TEMPLATES
    # =========================

    verbs_out = {}
    conjugations_out = {}

    for signature, verbs in signatures.items():
        rep = verbs[0]

        root = lemma_data[rep]["root"]
        ending = rep[len(root):]
        template = f"{root}:{ending}"

        # build conjugation table
        conj_table = defaultdict(lambda: defaultdict(list))

        for (mood, tense, person), ending_val in signature:
            conj_table[mood][tense].append([person, ending_val])

        conjugations_out[template] = conj_table

        # assign verbs
        for v in verbs:
            verbs_out[v] = {
                "root": lemma_data[v]["root"],
                "template": template
            }

    # =========================
    # SAVE
    # =========================

    verbs_file = OUTPUT_DIR / f"verbs-{lang}.json"
    conj_file = OUTPUT_DIR / f"conjugations-{lang}.json"

    with open(verbs_file, "w", encoding="utf-8") as f:
        json.dump(verbs_out, f, ensure_ascii=False, indent=4)

    with open(conj_file, "w", encoding="utf-8") as f:
        json.dump(conjugations_out, f, ensure_ascii=False, indent=4)

    logger.info(f"{lang}: saved ({len(verbs_out)} verbs)")


# =========================
# MAIN
# =========================

def main():
    for lang_dir in INPUT_DIR.iterdir():
        if lang_dir.is_dir():
            parse_language(lang_dir)

    logger.info("All languages processed.")


if __name__ == "__main__":
    main()
