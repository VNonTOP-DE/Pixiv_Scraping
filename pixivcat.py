import os
import time
import requests

with open("pixiv_ids.txt", "r") as file:
    image_ids = [line.strip() for line in file if line.strip().isdigit()]

save_folder = "pixiv_images"
os.makedirs(save_folder, exist_ok=True)

def download_image(url, save_path, max_retries=3):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://pixiv.cat/"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()

            # Only proceed if it's an image
            if "image" in response.headers.get("Content-Type", ""):
                content_length = int(response.headers.get("Content-Length", 0))
                downloaded_bytes = 0

                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            downloaded_bytes += len(chunk)

                # Verify the full file was downloaded
                if content_length > 0 and downloaded_bytes < content_length:
                    print(f"Incomplete download: {url}")
                    os.remove(save_path)  # Remove the partial file
                    return False

                print(f"✅ Downloaded: {save_path}")
                return True

            else:
                print(f"⚠️ Not an image or no content at {url}")
                return False

        except requests.exceptions.RequestException as e:
            if "502" in str(e):
                print(f"🔄 Retry {attempt + 1}/{max_retries} for 502 Bad Gateway: {url}")
                time.sleep(5)  # Wait before retrying
            else:
                print(f"❌ Error accessing {url}: {e}")
                return False

    print(f"❌ Skipping {url} after {max_retries} retries")
    return False

for x in image_ids:
    time.sleep(0.5)  # Reduce request rate

    jpg_url = f"https://pixiv.cat/{x}.jpg"
    png_url = f"https://pixiv.cat/{x}.png"
    png_alt_url = f"https://pixiv.cat/{x}-1.png"

    jpg_path = os.path.join(save_folder, f"{x}.jpg")
    png_path = os.path.join(save_folder, f"{x}.png")

    if download_image(jpg_url, jpg_path):
        continue
    if download_image(png_url, png_path):
        continue
    if download_image(png_alt_url, png_path):
        continue

    print(f"🚫 No valid image for {x}")
