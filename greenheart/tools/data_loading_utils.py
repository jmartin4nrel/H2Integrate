from pathlib import Path

import dill


def check_create_folder(filepath):
    path = Path(filepath)
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
        already_exists = False
    else:
        already_exists = True

    return already_exists


def dump_data_to_pickle(data, filepath):
    with Path.open(filepath, "wb") as f:
        dill.dump(data, f)


def load_dill_pickle(filepath):
    if isinstance(filepath, str):
        filepath = Path(filepath)
    with Path.open(filepath, "rb") as f:
        data = dill.load(f)
    return data
