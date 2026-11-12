"""Check datetime preservation through Dataset JSON-LD serialization."""
import argparse
import json
from pathlib import Path
import mlcroissant as mlc

parser = argparse.ArgumentParser()
parser.add_argument("--expect", choices=["baseline", "patched"], required=True)
args = parser.parse_args()
inputs = [
    "2024-03-18",
    "2024-03-18T00:00:00",
    "2024-03-18T12:00:00",
    "2024-03-18T00:00:00Z",
    "2024-03-18T00:00:00+09:00",
    "2024-03-18T00:00:00-05:30",
    "2024-03-18T12:00:00Z",
    "2024-03-18T00:00:00.000001+09:00",
]
standard_context = json.loads(Path('datasets/1.0/titanic/metadata.json').read_text(encoding='utf-8'))['@context']
results = []
for value in inputs:
    metadata = {
        "@context": standard_context,
        "@type": "Dataset", "name": "synthetic-date-roundtrip",
        "description": "Local synthetic date metadata.",
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "url": "https://example.org/dataset",
        **{key: value for key in ("dateCreated", "dateModified", "datePublished")},
    }
    dataset = mlc.Dataset(jsonld=metadata)
    serialized = dataset.metadata.to_json()
    encoded = json.dumps(serialized)
    restored = mlc.Dataset(jsonld=json.loads(encoded))
    comparisons = {}
    for attr in ("date_created", "date_modified", "date_published"):
        before = getattr(dataset.metadata, attr)
        after = getattr(restored.metadata, attr)
        comparisons[attr] = before == after and before.utcoffset() == after.utcoffset()
    results.append({"input": value, "output": {key: serialized[key] for key in
                    ("dateCreated", "dateModified", "datePublished")},
                    "fields_equal": comparisons, "pass": all(comparisons.values())})
print(json.dumps(results, indent=2), flush=True)
Path(args.expect+"-metadata.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
failed = [row["input"] for row in results if not row["pass"]]
expected = inputs[3:6] if args.expect == "baseline" else []
assert failed == expected, (failed, expected)
