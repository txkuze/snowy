import os
import pyzipper

def unzip_file(zip_path, password=None):
    try:
        extract_dir = "/tmp/unzipped"
        os.makedirs(extract_dir, exist_ok=True)

        with pyzipper.AESZipFile(zip_path, 'r') as zip_ref:
            if password:
                zip_ref.pwd = password.encode()
            zip_ref.extractall(extract_dir)

        # Only return full paths to extracted FILES (not directories)
        extracted = []
        for root, _, files in os.walk(extract_dir):
            for file in files:
                extracted.append(os.path.join(root, file))

        return extracted

    except RuntimeError as e:
        return f"❌  Failed to unzip: {e}"
    except Exception as e:
        return f"❌  Error: {e}"