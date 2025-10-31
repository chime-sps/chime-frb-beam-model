#!/usr/bin/env python3

import requests
import os
import time
import cfbm


here = cfbm.__file__.split("__init__.py")[0]

def download_file_from_web(url, destination, max_retries=3, initial_delay=2):
    """Download a file with retry logic for transient failures.

    Args:
        url: URL to download from
        destination: Path to save the file
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds between retries, doubles each attempt (default: 2)
    """
    session = requests.Session()

    for attempt in range(max_retries):
        try:
            response = session.get(url, stream=True, allow_redirects=True, timeout=30)

            # Check if the response is successful
            if response.status_code != 200:
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    print(f"Failed to download (status {response.status_code}), retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(f"Failed to download file from {url} after {max_retries} attempts. Status code: {response.status_code}")

            token = get_confirm_token(response)

            if token:
                # Extract file ID from URL for Google Drive retry logic
                file_id = url.split('/')[-2] if '/d/' in url else url.split('id=')[-1].split('&')[0]
                params = {"id": file_id, "confirm": token}
                response = session.get(url, params=params, stream=True, allow_redirects=True, timeout=30)

                # Check retry response status
                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        delay = initial_delay * (2 ** attempt)
                        print(f"Failed to download after token confirmation (status {response.status_code}), retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(f"Failed to download file from {url} after retry. Status code: {response.status_code}")

            save_response_content(response, destination)
            # Success - break out of retry loop
            if attempt > 0:
                print(f"Download succeeded on attempt {attempt + 1}")
            return

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                print(f"Network error: {e}, retrying in {delay} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                continue
            else:
                raise Exception(f"Failed to download file from {url} after {max_retries} attempts due to network error: {e}")


def get_confirm_token(response):
    for key, value in list(response.cookies.items()):
        if key.startswith("download_warning"):
            return value
    return None


def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    try:
        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
    except Exception as e:
        # Remove partial download on failure
        if os.path.exists(destination):
            os.remove(destination)
        raise Exception(f"Failed to save file to {destination}: {str(e)}")


def main():
    print("Downloading CHIME/FRB Beam Model")
    # Updated URLs to current server location
    file_ids = {
        "beam_XX_v1.h5": "https://ws-cadc.canfar.net/vault/files/AstroDataCitationDOI/CISTI.CANFAR/22.0005/data/beam_XX_v1.h5",
        "beam_YY_v1.h5": "https://ws-cadc.canfar.net/vault/files/AstroDataCitationDOI/CISTI.CANFAR/22.0005/data/beam_YY_v1.h5",
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

    # Verify both files exist and are the same size
    beam_xx_path = directory + "beam_XX_v1.h5"
    beam_yy_path = directory + "beam_YY_v1.h5"

    if os.path.isfile(beam_xx_path) and os.path.isfile(beam_yy_path):
        xx_size = os.path.getsize(beam_xx_path)
        yy_size = os.path.getsize(beam_yy_path)

        print(f"beam_XX_v1.h5: {xx_size} bytes")
        print(f"beam_YY_v1.h5: {yy_size} bytes")

        if xx_size != yy_size:
            raise Exception(
                f"File size mismatch: beam_XX_v1.h5 ({xx_size} bytes) != beam_YY_v1.h5 ({yy_size} bytes). "
                "The two beam model files should be the same size. One or both may be corrupted."
            )

        print(f"File size verification passed: both files are {xx_size} bytes")

    print("Download Complete")


if __name__ == "__main__":
    main()
