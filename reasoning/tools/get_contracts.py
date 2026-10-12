import json
import re
import zipfile
import pathlib

ZIP_PATH = "data/raw/data.zip"
OUT_DIR = pathlib.Path("data/raw")
HOW_MANY = 16

# 1. zip ke andar se CUADv1.json padho
with zipfile.ZipFile(ZIP_PATH) as z:
    data = json.loads(z.read("CUADv1.json"))

# 2. aisi lines dhundne ka pattern jo "1." ya "2.1" jaise section number se shuru hoti hain
numbered = re.compile(r"^\s*\d{1,2}(\.\d{1,2})?[\.\)]?\s+\S", re.MULTILINE)

# 3. sirf kaam ke contracts chuno: na bahut chhote, na bahut bade, aur numbered sections wale
good = []
for item in data["data"]:
    title = item["title"]
    text = item["paragraphs"][0]["context"]
    if 8000 <= len(text) <= 40000:
        n = len(numbered.findall(text))
        if n >= 12:
            good.append((n, title, text))

print("Kaam ke contracts mile:", len(good))

# 4. list mein se alag-alag jagah se HOW_MANY contracts uthao
good.sort(key=lambda g: -g[0])
step = max(1, len(good) // HOW_MANY)
chosen = good[::step][:HOW_MANY]

# 5. har contract ko .txt file mein save karo
for k, (n, title, text) in enumerate(chosen, start=1):
    name = f"r{k}_" + re.sub(r"[^A-Za-z0-9]+", "_", title)[:50] + ".txt"
    (OUT_DIR / name).write_text(text, encoding="utf-8")
    print(name, "-", n, "numbered lines")