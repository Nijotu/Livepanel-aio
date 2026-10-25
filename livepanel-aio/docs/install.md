# Installation details

## Requirements

Linux, Python 3.11+ with venv/pip, tmux 3.3+, Fastfetch, Starship, one of Fish/Bash/Zsh, ANSIWeather, playerctl, jq, bc, curl, fontconfig and librsvg's `rsvg-convert`. The installer adds Kitty for its `kitten` image helper; you can keep using Ghostty. A Nerd Font provides prompt glyphs. `tuptime` is optional for lifetime uptime; NVIDIA readings need the driver's `nvidia-smi`, AMD readings use sysfs. Unsupported sensors show unavailable.

`bash install.sh` uses pacman, apt or dnf for system dependencies. If missing from the selected repositories, Fastfetch (pinned 2.70.0, x86_64/aarch64), Starship (official installer) and ANSIWeather (1.19.0) are downloaded from their official projects. Python dependencies are installed in the app's own venv. This is an online installer, not an offline bundle.

On other distributions, install the requirements using your package manager, then run `bash install.sh --no-deps`. This flag skips system/helper downloads but still creates the venv and installs Python requirements. `--no-font` skips font installation. `--dry-run` prints planned paths without changes.

On a fresh interactive install, choose Fish, Bash or Zsh when prompted. Enter accepts the detected preferred shell; unsupported detection falls back to Bash. Use `--shell bash`, `--shell zsh` or `--shell fish` to skip the prompt. Noninteractive installs and `--dry-run` use the detected default without prompting. Your login shell is unchanged.

Fresh interactive installs also ask for a weather location in `City,CC` format. Enter keeps `London,GB`; `--location 'Paris,FR'` skips this question. Noninteractive installs use London unless overridden. Existing weather settings are preserved on reinstall. The question checks the format, not whether the weather provider can resolve the city.

Default locations:

- App: `~/.local/share/livepanel-aio/`
- Configs: `~/.config/livepanel-aio/`
- Command: `~/.local/bin/livepanel-aio`
- Font: `~/.local/share/fonts/livepanel-aio/`
- Session cache: `~/.cache/livepanel-aio/`

XDG data/config/cache variables are honored. `LIVEPANEL_CONFIG_DIR` and `LIVEPANEL_BIN_DIR` override config and command paths. Paths should remain stable after installation.

On reinstall, existing configs stay in place; new defaults are saved as `.example` files. The previous app directory is retained as a timestamped backup. `--shell`/`--location` initialize new settings only; edit an existing `settings.toml` to change them later. The installer uses the saved shell for dependencies and autostart on reinstall, even if `--shell` differs.

## Font selection

The installer copies the supplied OTF and refreshes the font cache. Applications still need to select it:

- **Ghostty:** `font-family = DroidSansMono Cachy Nerd Font` in `~/.config/ghostty/config`.
- **Kitty:** `font_family DroidSansMono Cachy Nerd Font` in `~/.config/kitty/kitty.conf`.
- **Konsole:** Edit Current Profile → Appearance → Font; choose the family.
- **GNOME Terminal:** Preferences → your profile → Text → Custom font; choose the family.

Open a new terminal after changing the font. `fc-match 'DroidSansMono Cachy Nerd Font'` should resolve to the installed font. Another Nerd Font works with the default public prompt, but not necessarily the custom Cashy glyph. With `--no-font`, choose an existing Nerd Font yourself.

Manual installation if needed:

```sh
mkdir -p ~/.local/share/fonts/livepanel-aio
cp fonts/DroidCachyNerd-Regular.otf ~/.local/share/fonts/livepanel-aio/
fc-cache -f ~/.local/share/fonts/livepanel-aio
```

## Default on opening a terminal

Run `bash install.sh --autostart`. For a fresh install, optionally add `--shell bash`, `--shell zsh` or `--shell fish`; reinstalls use the saved setting. Fish gets a file in `~/.config/fish/conf.d/`; Bash/Zsh get a marked block in their interactive rc file. These hooks run only in interactive local shells outside tmux/Livepanel. An existing rc file is backed up before editing. With Zsh, a custom `ZDOTDIR` is honored.

To disable just autostart, remove `livepanel-aio.fish` from Fish's `conf.d`, or remove the `BEGIN LIVEPANEL AIO` through `END LIVEPANEL AIO` block from your Bash/Zsh rc file. Disable an older Livepanel hook before enabling the new one.

## Isolated trial

For the simplest trial, install without `--autostart`; the AIO uses a separate name from the old app. System dependencies and fonts may still be installed.

To test with separate paths and no font/system changes, first have the dependencies available, then run these commands **in Bash** from the extracted folder:

```bash
trial="$HOME/.local/share/livepanel-aio-trial"
XDG_DATA_HOME="$trial/data" \
LIVEPANEL_CONFIG_DIR="$trial/config/livepanel-aio" \
LIVEPANEL_BIN_DIR="$trial/bin" \
bash install.sh --no-deps --no-font
"$trial/bin/livepanel-aio"
```

Python packages are still downloaded into that trial app's venv. To remove it after closing the session:

```bash
bash "$trial/data/livepanel-aio/uninstall.sh" --purge-config
```

No trial autostart is added. Do not run the installer with `sudo`; it handles package-manager elevation itself.

## Remove a normal installation

Exit running AIO sessions, then:

```sh
bash ~/.local/share/livepanel-aio/uninstall.sh
```

This removes its app, command and managed autostart hook. Configs remain; add `--purge-config` to remove them. System packages, the font and timestamped backups are kept because you may still use them. To remove the font later, first select another terminal font, then delete its `~/.local/share/fonts/livepanel-aio/` folder and run `fc-cache -f`.
