#!/usr/bin/env python3
"""
Discord bot pour générer un mod FS25 via une commande slash /generate_mod
Utilisation sécurisée :
- FOURNIR le token via variable d'environnement DISCORD_TOKEN (NE PAS hardcoder)
- Optionnel : définir GUILD_ID pour enregistrement rapide (dev)
"""
import os
import tempfile
import traceback
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from generate_mod import create_mod, zip_mod  # module précédent

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise RuntimeError("Attendre: définis la variable d'environnement DISCORD_TOKEN")

# Optionnel: limiter aux guildes de développement pour enregistrement instantané
GUILD_ID = int(os.getenv("GUILD_ID")) if os.getenv("GUILD_ID") else None
ALLOWED_ROLE_NAME = os.getenv("ALLOWED_ROLE_NAME")  # si défini, seuls les membres avec ce rôle peuvent exécuter la commande

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user} (id: {bot.user.id})")
    # enregistrer la commande dans une guild (si fournie) pour propagation immédiate
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        try:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print("Commandes synchronisées dans la guild:", GUILD_ID)
        except Exception as e:
            print("Échec sync guild:", e)
    else:
        # sync global (peut prendre jusqu'à 1 heure pour apparaître)
        try:
            await bot.tree.sync()
            print("Commandes synchronisées globalement")
        except Exception as e:
            print("Échec sync global (normal en dev):", e)

# Définit la commande /generate_mod
@bot.tree.command(name="generate_mod", description="Génère un mod FS25 et renvoie un ZIP")
@app_commands.describe(name="Nom du mod", author="Auteur", version="Version", zip="Créer un zip à envoyer")
async def generate_mod(interaction: discord.Interaction, name: str, author: str = "Auteur", version: str = "1.0.0.0", zip: bool = True):
    # contrôle d'accès simple
    if ALLOWED_ROLE_NAME:
        member = interaction.user
        if not any(r.name == ALLOWED_ROLE_NAME for r in getattr(member, "roles", [])):
            await interaction.response.send_message("Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
            return

    # limiter longueur et caractères du nom pour éviter abus
    if len(name) > 64:
        await interaction.response.send_message("Nom trop long (max 64 caractères).", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)  # indique que le bot travaille

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            mod_dir = create_mod(name, author, version, out)
            zip_path = out / f"{name}.zip"
            zip_mod(mod_dir, zip_path)

            # taille limite (ex: 10 MB) — adapte selon besoin
            MAX_SEND_BYTES = 10 * 1024 * 1024
            if zip_path.stat().st_size > MAX_SEND_BYTES:
                await interaction.followup.send("Le fichier généré dépasse la taille maximale autorisée.", ephemeral=True)
                return

            await interaction.followup.send(content=f"Mod généré : {name}", file=discord.File(fp=str(zip_path), filename=f"{name}.zip"))
    except Exception as e:
        tb = traceback.format_exc()
        print("Erreur generate_mod:", tb)
        await interaction.followup.send(f"Erreur lors de la génération: {e}", ephemeral=True)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)