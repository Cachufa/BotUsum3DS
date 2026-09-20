# BotUsum3DS

Bot para shiny hunting en Pokémon Ultra Sol / Ultra Luna (Azahar). Fase 1: Poipole.

Este archivo es la memoria de proyecto. Lo leen Claude Code y Grok (compatibilidad Claude: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/`).

## Qué es este repo

Automatización para cazar shinys en USUM. Los dumps (`.3ds`, copias `main-*-shiny-N`) viven en `resources/` y **no son código**.

## Dónde está qué

| Ruta | Uso |
|------|-----|
| `CLAUDE.md` | Normas y contexto del proyecto (este archivo) |
| `.claude/rules/` | Normas modulares (se cargan todas) |
| `.claude/plans/` | Planes de trabajo, specs, checklists |
| `resources/` | ROMs, copias shiny — no commitear dumps |
| `README.md` | Descripción corta para humanos |

## Cómo trabajar aquí

- **No hay commit ni push sin permiso expreso del usuario.** Ni `git commit`, ni `git push`, ni `--amend`, ni staging “por si acaso”. Esperar una frase clara del tipo “haz commit” / “commitea esto”.
- Todo **código, identificadores, comentarios, docstrings, mensajes de commit y texto en el repo** van en **inglés**. El chat con el usuario puede ir en español.
- Antes de implementar, lee las reglas en `.claude/rules/` y el plan activo en `.claude/plans/` si existe.
- Plans live in `.claude/plans/<name>.md`, in English. One active plan at a time unless stated otherwise.
- No inventes arquitectura. Propón y documenta en un plan antes de crear un árbol grande de carpetas.
- No toques dumps en `resources/` salvo que el usuario lo pida. No copies ROMs a otros sitios.
- Código nuevo: claro, acotado al pedido, sin refactors de relleno.

## Idioma

- Chat: español (salvo que el usuario pida otra cosa).
- Repo: inglés — código, comentarios, docs en el árbol de código, nombres de archivos de implementación.

## Comandos

- Hunt (desde la raíz del repo): `python3 -m botusum`
- Si faltan el ROM de Ultra Luna o Azahar.app: error en stderr y exit `1`
- Accessibility de macOS para teclado (`pynput`). RPC de Azahar en UDP 45987.
- Detalle: `.claude/rules/toolchain.md`
- Umbrella: `.claude/plans/usum-shiny-loop.md`
