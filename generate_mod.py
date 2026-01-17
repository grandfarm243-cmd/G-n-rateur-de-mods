#!/usr/bin/env python3
"""
Générateur de mod FS25 - module réutilisable.
Fonctions exportées: create_mod(mod_name, author, version, out_dir) -> Path, zip_mod(mod_dir, zip_path)
Ne gère pas les entrées non sûres : le caller doit valider/sanitiser.
"""
import os
import zipfile
import base64
from pathlib import Path

ICON_BASE64 = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="

MODDESC_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<modDesc descVersion="61">
    <title>{title}</title>
    <description>{description}</description>
    <version>{version}</version>
    <author>{author}</author>
    <script file="scripts/main.lua" />
    <icon filename="icon.png" />
</modDesc>
"""

MAIN_LUA_TEMPLATE = """-- Script d'exemple pour le mod {title}
local {id} = {{}}
{id}.modName = "{title}"

function {id}:loadMap(name)
    print("[" .. self.modName .. "] loaded map: " .. tostring(name))
end

addModEventListener({id})
"""

def safe_mod_id(name: str) -> str:
    s = ''.join(ch if ch.isalnum() else '_' for ch in name)
    if not s:
        s = "mod"
    if s[0].isdigit():
        s = '_' + s
    return s

def write_icon(path: Path):
    with open(path, "wb") as f:
        f.write(base64.b64decode(ICON_BASE64))

def create_mod(mod_name: str, author: str, version: str, out_dir: Path) -> Path:
    """
    Crée la structure du mod sous out_dir/<mod_name> et retourne le Path du dossier.
    Lève une exception si le dossier existe.
    """
    mod_dir = out_dir / mod_name
    if mod_dir.exists():
        raise FileExistsError(f"{mod_dir} existe déjà")
    (mod_dir / "scripts").mkdir(parents=True)
    # écrire modDesc.xml
    modDesc = MODDESC_TEMPLATE.format(
        title=mod_name,
        description=f"Mod généré automatiquement : {mod_name}",
        version=version,
        author=author
    )
    (mod_dir / "modDesc.xml").write_text(modDesc, encoding="utf-8")
    lua_id = safe_mod_id(mod_name)
    main_lua = MAIN_LUA_TEMPLATE.format(title=mod_name, id=lua_id)
    (mod_dir / "scripts" / "main.lua").write_text(main_lua, encoding="utf-8")
    write_icon(mod_dir / "icon.png")
    return mod_dir

def zip_mod(mod_dir: Path, zip_path: Path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(mod_dir):
            for file in files:
                full = Path(root) / file
                # arcname: preserve folder structure starting from mod_dir.name
                arcname = full.relative_to(mod_dir.parent)
                zf.write(full, arcname=str(arcname))