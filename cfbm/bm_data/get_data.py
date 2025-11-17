#!/usr/bin/env python3

import requests
import os
import cfbm


here = cfbm.__file__.split("__init__.py")[0]

def download_file_from_web(url, destination):
    session = requests.Session()
    response = session.get(url, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {"id": id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def get_confirm_token(response):
    for key, value in list(response.cookies.items()):
        if key.startswith("download_warning"):
            return value
    return None


def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def main():
    print("Downloading CHIME/FRB Beam Model")
    # Download from GitHub Release assets (keeps files out of git repo to avoid bloat)
    # Release version matches beam model data version (indexed by date)
    RELEASE_TAG = "2022.5.1"
    file_ids = {
        "beam_XX_v1.h5": f"https://github.com/chime-sps/chime-frb-beam-model/releases/download/{RELEASE_TAG}/beam_XX_v1.h5",
        "beam_YY_v1.h5": f"https://github.com/chime-sps/chime-frb-beam-model/releases/download/{RELEASE_TAG}/beam_YY_v1.h5",
    }

    directory = here + "/bm_data/"
    if not os.path.exists(directory):
        print("Making beam model data directory at {}...".format(directory))
        os.makedirs(directory)

    for filename in file_ids.keys():
        print("Fetching: {}".format(filename))
        destination = directory + "{}".format(filename)
        if not os.path.isfile(destination):
            download_file_from_web(file_ids[filename], destination)
        else:
            print(f"{filename} already exists, skipping download")

    print("Download Complete")


if __name__ == "__main__":
    main()
