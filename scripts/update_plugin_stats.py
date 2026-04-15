#!/usr/bin/env python3
import requests
import re
import os
import hashlib
import yaml
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def load_plugin_config():
    """Load plugin ID from plugin/src/settings.yml"""
    settings_path = Path('plugin/src/settings.yml')
    if not settings_path.exists():
        print(f"❌ {settings_path} not found")
        return None

    with open(settings_path) as f:
        settings = yaml.safe_load(f)

    plugin_id = str(settings.get('id', '')).strip()
    if not plugin_id:
        print("❌ No 'id' found in plugin/src/settings.yml")
        return None

    return {
        'plugin_ids': [plugin_id],
        'section_title': '🚀 TRMNL Plugin',
        'images_dir': 'assets/plugin-images',
    }


def download_image(url: str, save_path: str, max_retries=3):
    """Download an image from URL and save it locally with retry logic"""
    for attempt in range(max_retries):
        try:
            headers = {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            new_content = response.content
            new_hash = hashlib.md5(new_content).hexdigest()

            if os.path.exists(save_path):
                with open(save_path, 'rb') as f:
                    old_hash = hashlib.md5(f.read()).hexdigest()
                if old_hash == new_hash:
                    print(f"  ↪ Unchanged: {os.path.basename(save_path)}")
                    return True

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(new_content)
            print(f"  ✓ Updated: {os.path.basename(save_path)}")
            return True

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️  Retry {attempt + 1}/{max_retries - 1} for {os.path.basename(save_path)}")
            else:
                print(f"  ✗ Failed to download {os.path.basename(save_path)} after {max_retries} attempts: {e}")
                return False

    return False


def get_image_extension(url: str):
    parsed = urlparse(url)
    _, ext = os.path.splitext(parsed.path)
    return ext if ext else '.png'


def fetch_plugin_data(plugin_id: str, max_retries=3):
    url = f"https://trmnl.com/recipes/{plugin_id}.json"
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️  Retry {attempt + 1}/{max_retries - 1} for plugin data")
            else:
                print(f"  ✗ HTTP Error fetching plugin data after {max_retries} attempts: {e}")
                return None
        except ValueError as e:
            print(f"  ✗ JSON parsing error for plugin {plugin_id}: {e}")
            return None
    return None


def process_plugin_images(plugin_id: str, plugin_data: dict, images_dir: str):
    if not plugin_data:
        return None

    plugin = plugin_data.get('data', {})
    icon_url = plugin.get('icon_url', '')
    screenshot_url = plugin.get('screenshot_url', '')
    local_paths = {'icon': None, 'screenshot': None}
    download_success = True

    if icon_url:
        icon_path = os.path.join(images_dir, f"{plugin_id}_icon{get_image_extension(icon_url)}")
        if download_image(icon_url, icon_path):
            local_paths['icon'] = icon_path
        else:
            download_success = False

    if screenshot_url:
        screenshot_path = os.path.join(images_dir, f"{plugin_id}_screenshot{get_image_extension(screenshot_url)}")
        if download_image(screenshot_url, screenshot_path):
            local_paths['screenshot'] = screenshot_path
        else:
            download_success = False

    return local_paths if download_success else None


def generate_plugin_section(data, plugin_id: str, image_paths: dict):
    if not data or not data.get('data'):
        return f"""
## 🔒 Plugin ID: {plugin_id}

**Status**: ⏳ Not yet published on TRMNL or API unavailable

**Plugin URL**: https://trmnl.com/recipes/{plugin_id}

---
"""

    plugin = data['data']
    icon_path = image_paths.get('icon') if image_paths else plugin.get('icon_url', '')
    screenshot_path = image_paths.get('screenshot') if image_paths else plugin.get('screenshot_url', '')
    name = plugin.get('name', 'Unknown Plugin')
    description = plugin.get('author_bio', {}).get('description', 'No description available')

    return f"""
## <img src="{icon_path}" alt="{name} icon" width="32"/> [{name}](https://trmnl.com/recipes/{plugin_id})

![Installs](https://trmnl-badges.gohk.xyz/badge/installs?recipe={plugin_id}) ![Forks](https://trmnl-badges.gohk.xyz/badge/forks?recipe={plugin_id})

![{name} screenshot]({screenshot_path})

### Description
{description}

---
"""


def update_readme(plugin_sections: str, section_title: str):
    try:
        with open('README.md', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = "# Project README\n\n"

    start_marker = "<!-- PLUGIN_STATS_START -->"
    end_marker = "<!-- PLUGIN_STATS_END -->"
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    new_content = f"{start_marker}\n## {section_title}\n\n*Last updated: {timestamp}*\n\n{plugin_sections}\n{end_marker}"

    if start_marker in content and end_marker in content:
        pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
        updated_content = re.sub(pattern, new_content, content, flags=re.DOTALL)
    else:
        updated_content = content + "\n\n" + new_content + "\n"

    with open('README.md', 'w') as f:
        f.write(updated_content)


def main():
    config = load_plugin_config()
    if not config:
        return

    plugin_ids = config['plugin_ids']
    section_title = config['section_title']
    images_dir = config['images_dir']

    print(f"📋 Tracking plugin(s): {', '.join(plugin_ids)}")
    print(f"📁 Images: {images_dir}\n")

    plugin_sections = []
    for idx, plugin_id in enumerate(plugin_ids, 1):
        print(f"🔍 [{idx}/{len(plugin_ids)}] Processing plugin: {plugin_id}")
        data = fetch_plugin_data(plugin_id)
        image_paths = None
        if data and data.get('data'):
            image_paths = process_plugin_images(plugin_id, data, images_dir)
            print(f"  {'✓ Processed' if image_paths else '⚠️  Images failed'}")
        else:
            print(f"  ⏳ Not published yet or API error")
        plugin_sections.append(generate_plugin_section(data, plugin_id, image_paths))
        print()

    update_readme("\n".join(plugin_sections), section_title)
    print("✅ README.md updated successfully!")


if __name__ == "__main__":
    main()
