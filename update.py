import yaml
# Configuración
build_yaml_path = "./build.yaml"
# 0. Actualizar build.yaml con versión y changelog
def update_build_yaml(build_yaml_path, version, changelog_text):
    with open(build_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["version"] = version
    data["changelog"] = changelog_text
    with open(build_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)
import os
import zipfile
import shutil
import json
import hashlib
import re
from datetime import datetime, timezone

# Configuración
plugin_name = "SpotDLPlugin"
publish_dir = f"./{plugin_name}/bin/Debug/net8.0/publish"
temp_dir = "./temp"
os.makedirs(temp_dir, exist_ok=True)
meta_json_path = os.path.join(temp_dir, "meta.json")
changelog_path = "./changelog.md"
repository_json_path = "./spotdlplugin-repository.json"
github_repo = "AorsiniYT/SpotDLPlugin"

# 1. Extraer la última versión del changelog
def get_latest_changelog(changelog_path):
    with open(changelog_path, "r", encoding="utf-8") as f:
        changelog = f.read()
    match = re.search(r"## \[(.*?)\] - (.*?)\n(.*?)(?=\n## |\Z)", changelog, re.DOTALL)
    if match:
        version = match.group(1)
        date = match.group(2)
        changelog_text = match.group(3).strip()
        return version, date, changelog_text
    else:
        raise Exception("No se encontró una versión válida en el changelog.")

# 2. Actualizar meta.json con el changelog y versión
def update_meta_json(meta_json_path, version, changelog_text):
    meta = {
        "category": "Metadata",
        "changelog": changelog_text,
        "description": "Plugin for Jellyfin that integrates SpotDL for music management and downloading.",
        "guid": "b7e2a1c2-9e4a-4b2a-8c1d-2f3e4a5b6c7d",
        "imageUrl": "https://github.com/AorsiniYT/SpotDLPlugin/raw/main/spotdlplugin.png",
        "name": "SpotDLPlugin",
        "overview": "Download and manage your music with SpotDL in Jellyfin.",
        "owner": "AorsiniYT",
        "targetAbi": "10.6.0.0",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": version
    }
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
    # El archivo se cierra aquí antes de copiarlo en la función create_release_zip
    return meta

# 3. Crear el ZIP de la release
def create_release_zip(publish_dir, meta_json_path, plugin_name, version):
    output_zip = os.path.join(temp_dir, f"{plugin_name.lower()}_{version}.zip")
    # meta.json ya está en temp_dir
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Agregar DLLs directamente desde publish_dir
        for file in os.listdir(publish_dir):
            if file.endswith(".dll"):
                zipf.write(os.path.join(publish_dir, file), file)
        # Agregar meta.json desde temp_dir
        zipf.write(meta_json_path, "meta.json")
    return output_zip

# 4. Calcular checksum del ZIP
def get_checksum(file_path):
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def update_repository_json(repository_json_path, meta, version, changelog_text, source_url, checksum):
    print("Actualizando spotdlplugin-repository.json...")
    with open(repository_json_path, "r", encoding="utf-8") as f:
        repo = json.load(f)
    # Soporte para lista o dict
    if isinstance(repo, list):
        if repo and "versions" in repo[0]:
            versions = repo[0]["versions"]
        else:
            versions = []
    else:
        versions = repo.setdefault("versions", [])
    found = False
    for i, v in enumerate(versions):
        if v["version"] == version:
            versions[i] = {
                "version": version,
                "changelog": changelog_text,
                "targetAbi": meta.get("targetAbi", ""),
                "sourceUrl": source_url,
                "checksum": checksum,
                "timestamp": meta["timestamp"]
            }
            found = True
            print(f"Versión {version} actualizada en el repositorio.")
            break
    if not found:
        versions.insert(0, {
            "version": version,
            "changelog": changelog_text,
            "targetAbi": meta.get("targetAbi", ""),
            "sourceUrl": source_url,
            "checksum": checksum,
            "timestamp": meta["timestamp"]
        })
        print(f"Versión {version} agregada al repositorio.")
    with open(repository_json_path, "w", encoding="utf-8") as f:
        json.dump(repo, f, indent=4)

def get_previous_version(repository_json_path):
    with open(repository_json_path, "r", encoding="utf-8") as f:
        repo = json.load(f)
    # Soporte para lista o dict
    if isinstance(repo, list):
        if repo and "versions" in repo[0]:
            versions = repo[0]["versions"]
        else:
            versions = []
    else:
        versions = repo.get("versions", [])
    if len(versions) > 1:
        return versions[1]["version"]
    return None

def format_github_release(version, date, changelog_text, previous_version=None):
    # Agrupa el changelog por secciones si se usan encabezados tipo ###
    sections = re.findall(r"### (.*?)\n(.*?)(?=\n### |\Z)", changelog_text, re.DOTALL)
    description = f"## What's Changed\n\n"
    for title, content in sections:
        emoji = ""
        if "feature" in title.lower(): emoji = "✨ "
        elif "fix" in title.lower(): emoji = "🔧 "
        elif "change" in title.lower() or "refactor" in title.lower(): emoji = "⚙️ "
        description += f"### {emoji}{title.strip()}\n{content.strip()}\n\n"
    if not sections:
        description += changelog_text + "\n\n"
    description += "## Contributors\n* By @AorsiniYT\n"
    if previous_version:
        description += f"\n**Full Changelog**: https://github.com/{github_repo}/compare/{previous_version}...{version}\n"
    return description

import subprocess

def publish_github_release_cli(version, description, zip_path):
    # Si el tag existe, borrarlo
    tag_exists = subprocess.run(["git", "tag", "-l", version], capture_output=True, text=True)
    if tag_exists.stdout.strip() == version:
        subprocess.run(["git", "tag", "-d", version], check=True)
        subprocess.run(["git", "push", "origin", f":refs/tags/{version}"], check=True)
    # Si el release existe, borrarlo
    release_exists = subprocess.run(["gh", "release", "view", version], capture_output=True)
    if release_exists.returncode == 0:
        subprocess.run(["gh", "release", "delete", version, "--yes"], check=True)
    # Crear el tag
    subprocess.run(["git", "tag", version], check=True)
    subprocess.run(["git", "push", "origin", version], check=True)
    # Crear el release con gh CLI
    release_cmd = [
        "gh", "release", "create", version,
        zip_path,
        "--title", f"{plugin_name} {version}",
        "--notes", description
    ]
    subprocess.run(release_cmd, check=True)
    # Obtener la URL del release
    url_cmd = ["gh", "release", "view", version, "--json", "assets", "--jq", ".assets[0].url"]
    result = subprocess.run(url_cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


if __name__ == "__main__":
    print("Obteniendo changelog y versión...")
    version, date, changelog_text = get_latest_changelog(changelog_path)
    print(f"Versión detectada: {version}")
    print("Actualizando build.yaml...")
    update_build_yaml(build_yaml_path, version, changelog_text)
    print("Creando meta.json...")
    meta = update_meta_json(meta_json_path, version, changelog_text)
    print("Empaquetando DLLs y meta.json en ZIP...")
    output_zip = create_release_zip(publish_dir, meta_json_path, plugin_name, version)
    print(f"ZIP generado: {output_zip}")
    print("Calculando checksum...")
    checksum = get_checksum(output_zip)
    print("Leyendo versión anterior del repositorio...")
    previous_version = get_previous_version(repository_json_path)
    print("Formateando descripción para el release...")
    description = format_github_release(version, date, changelog_text, previous_version)
    print("Actualizando spotdlplugin-repository.json...")
    update_repository_json(repository_json_path, meta, version, changelog_text, f"", checksum)
    print("Sincronizando repositorio con remoto...")
    subprocess.run(["git", "pull"], check=True)
    # Buscar el commit más antiguo con el mismo mensaje
    commit_msg = f"Update repository for version {version}"
    result = subprocess.run(["git", "log", "--reverse", "--pretty=format:%H:%s"], capture_output=True, text=True)
    found_commit = None
    for line in result.stdout.splitlines():
        if line.endswith(f":{commit_msg}"):
            found_commit = line.split(':')[0]
            break
    if found_commit:
        print(f"Commit más antiguo encontrado: {found_commit}. Realizando reset suave...")
        subprocess.run(["git", "reset", "--soft", found_commit + "^"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print("Commit antiguo eliminado y reemplazado. Publicando con push --force...")
        subprocess.run(["git", "push", "--force"], check=True)
    else:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
    print("Repositorio sincronizado y cambios publicados.")
    print("Publicando release en GitHub...")
    source_url = publish_github_release_cli(version, description, output_zip)
    print(f"URL del release: {source_url}")
    update_repository_json(repository_json_path, meta, version, changelog_text, source_url, checksum)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"Add release URL for version {version}"], check=False)
    subprocess.run(["git", "push"], check=True)
    print("Proceso completado correctamente.")