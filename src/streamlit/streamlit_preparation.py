import argparse
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.append("./")
sys.path.append("../../")

from src.config import *
from src.taxonomy.taxonomy import Taxonomy
from src.utilities import init_logger, printt

logger = init_logger(STREAMLIT_PATH + STREAMLIT_LOG_FILE, logger_name="taxonomy")
logfile = open(STREAMLIT_PATH + STREAMLIT_LOG_FILE, "w+")


def initialize():
    printt("Reading files...")
    files = pd.read_parquet(FILES_PATH)

    taxonomy = Taxonomy()
    printt("Loading graph...")
    taxonomy.load_graph(HGRAPH_PATH)
    printt("Loading mapping...")
    taxonomy.set_taxonomy(mapping="content_extended")
    # printt('Loading lexical parser...')
    # taxonomy.get_head('CommonsRoot')

    return files, taxonomy


def queryFile(file, how="heuristics"):
    """
    Given one file, a row of the files DataFrame, queries recursively all
    the categories and returns the final labels.
    """

    labels = set()
    for category in file.categories:
        logger.debug(f"Starting search for category {category}")
        cat_labels = taxonomy.get_label(category, how=how, debug=True)
        logger.debug(
            f"Ending search for category {category} with resulting labels {cat_labels}"
        )
        logger.debug(f"---------------------------------------------------")
        labels |= cat_labels
    logger.debug(f"Final labels: {labels}")
    log = logfile.read()
    return labels, log


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--n", help="size of the sample")
    parser.add_argument("-s", "--seed", help="random seed")
    parser.add_argument("-H ", "--how", help="querying scheme")
    args = parser.parse_args()

    files, taxonomy = initialize()

    n = int(args.n) if args.n else 1000
    seed = int(args.seed) if args.seed else 0
    how = args.how if args.how else "heuristics"
    files_sample = files.sample(n, random_state=seed)
    tqdm.pandas()
    files_sample["labels_true"] = [[] for _ in range(len(files_sample))]
    files_sample[["labels_pred", "log"]] = files_sample.progress_apply(
        lambda x: queryFile(x, how=how), axis=1, result_type="expand"
    )
    # Dict storing evaluations
    printt("Saving file..")
    files_sample["labels_pred"] = files_sample.apply(
        lambda x: {label: None for label in x.labels_pred}, axis=1
    )
    files_sample.to_json(STREAMLIT_PATH + f"files_{seed}_{n}_{how}.json.bz2")
