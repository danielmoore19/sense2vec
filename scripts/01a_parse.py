#!/usr/bin/env python
import spacy
from spacy.tokens import DocBin
import plac
from wasabi import msg
from pathlib import Path
import tqdm


@plac.annotations(
    in_file=("Path to input file", "positional", None, str),
    out_dir=("Path to output directory", "positional", None, str),
    spacy_model=("Name of spaCy model to use", "positional", None, str),
    n_process=("Number of processes (multiprocessing)", "option", "n", int),
    max_docs=("Maximum docs per batch",  "option", "m", int),
)
def main(in_file, out_dir, spacy_model="en_core_web_sm", n_process=1, max_docs=10**7):
    """
    Step 1: Parse raw text with spaCy

    Expects an input file with one sentence per line and will output a .spacy
    file of the parsed collection of Doc objects (DocBin).
    """
    input_path = Path(in_file)
    output_path = Path(out_dir)
    if not input_path.exists():
        msg.fail("Can't find input file", in_file, exits=1)
    if not output_path.exists():
        output_path.mkdir(parents=True)
        msg.good(f"Created output directory {out_dir}")
    nlp = spacy.load(spacy_model)
    msg.info(f"Using spaCy model {spacy_model}")
    doc_bin = DocBin(attrs=["POS", "TAG", "DEP", "ENT_TYPE", "ENT_IOB"])
    msg.text("Preprocessing text...")
    count = 0
    batch_num = 0
    with input_path.open("r", encoding="utf8") as texts:
        docs = nlp.pipe(texts, n_process=n_process)
        for doc in tqdm.tqdm(docs, desc="Docs", unit=""):
            if count < max_docs:
                doc_bin.add(doc)
                count += 1
                output_file = output_path / f"{input_path.stem}.spacy"
            else:
                batch_num += 1
                count = 0
                msg.good(f"Processed {len(doc_bin)} docs")
                doc_bin_bytes = doc_bin.to_bytes()
                output_file = output_path / f"{input_path.stem}-{batch_num}.spacy"
                with output_file.open("wb") as f:
                    f.write(doc_bin_bytes)
                msg.good(f"Saved parsed docs to file", output_file.resolve())
                doc_bin = DocBin(attrs=["POS", "TAG", "DEP", "ENT_TYPE", "ENT_IOB"])
        with output_file.open("wb") as f:
            batch_num += 1
            output_file = output_path / f"{input_path.stem}-{batch_num}.spacy"
            doc_bin_bytes = doc_bin.to_bytes()
            f.write(doc_bin_bytes)
            msg.good(f"Complete. Saved final parsed docs to file", output_file.resolve())

if __name__ == "__main__":
    plac.call(main)
