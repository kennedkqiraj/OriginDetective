from functools import lru_cache
from pathlib import Path
import pandas as pd

VN_NAMES = {"vietnam", "viet nam", "socialist republic of viet nam"}
VN_CODES = {"vn"}

def _norm(s):
    return (str(s) if s is not None else "").strip().lower()

@lru_cache(maxsize=1)
def load(csv_path="config/manufacturers.csv"):
    p = Path(csv_path)
    if not p.exists():
        # Empty DF with expected structure
        return pd.DataFrame(columns=["manufacturer_id", "name", "country", "country_code",
                                     "_id_norm", "_name_norm", "_country_norm", "_cc_norm"])

    df = pd.read_csv(p, dtype=str).fillna("")

    # >>> RENAME PATCH (map your headers to expected names) <<<
    df = df.rename(columns={
        "Manufacturers: name": "name",
        "Country of location": "country",
        # keep others as-is; we don't need Product Category or Location
    })

    # Ensure all expected source cols exist
    for col in ["manufacturer_id", "name", "country", "country_code"]:
        if col not in df.columns:
            df[col] = ""

    # Always build helper columns
    df["_id_norm"] = df["manufacturer_id"].map(_norm)
    df["_name_norm"] = df["name"].map(_norm)
    df["_country_norm"] = df["country"].map(_norm)
    df["_cc_norm"] = df["country_code"].map(_norm)

    return df

def lookup(name="", manufacturer_id="", csv_path="config/manufacturers.csv"):
    df = load(csv_path)
    name_n = _norm(name)
    id_n = _norm(manufacturer_id)

    cand = df
    if id_n:
        cand = cand[cand["_id_norm"] == id_n]
    if name_n and cand.empty:
        cand = df[df["_name_norm"] == name_n]

    if cand.empty:
        return {"found": False, "is_vietnam": False, "match": None}

    row = cand.iloc[0]
    is_vn = (row["_cc_norm"] in VN_CODES) or (row["_country_norm"] in VN_NAMES)
    match = row.drop(labels=[c for c in row.index if c.startswith("_")]).to_dict()
    return {"found": True, "is_vietnam": is_vn, "match": match}
