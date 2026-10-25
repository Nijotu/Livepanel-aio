#!/usr/bin/env bash
# One installer. System packages via distro manager; app files stay user-local.
set -euo pipefail
src="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app="${XDG_DATA_HOME:-$HOME/.local/share}/livepanel-aio"
config="${LIVEPANEL_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/livepanel-aio}"
bindir="${LIVEPANEL_BIN_DIR:-$HOME/.local/bin}"
shell_choice=""
location=""
deps=1; font=1; autostart=0; dry=0
while (($#)); do
    case "$1" in
        --no-deps) deps=0;;
        --no-font) font=0;;
        --autostart) autostart=1;;
        --dry-run) dry=1;;
        --shell) shell_choice="${2:?missing shell}"; shift;;
        --location) location="${2:?missing location}"; shift;;
        --help) printf '%s\n' 'Usage: bash install.sh [--shell fish|bash|zsh] [--location City,CC] [--autostart] [--no-deps] [--no-font] [--dry-run]'; exit 0;;
        *) printf 'Unknown option: %s\n' "$1" >&2; exit 2;;
    esac
    shift
done
case "$shell_choice" in ''|fish|bash|zsh) ;; *) echo 'Choose fish, bash or zsh.' >&2; exit 2;; esac
# Existing settings remain authoritative on upgrades, including dependencies
# and the shell receiving an optional autostart hook.
if [[ -f "$config/settings.toml" ]]; then
    if ! saved_shell=$(python3 - "$config/settings.toml" <<'PY'
import sys
try:
    import tomllib
    with open(sys.argv[1], 'rb') as f:
        shell = tomllib.load(f)['shell']
    if shell not in ('fish', 'bash', 'zsh'):
        raise ValueError('shell must be fish, bash or zsh')
    print(shell)
except Exception as exc:
    print(f'Cannot read existing shell setting: {exc}', file=sys.stderr)
    sys.exit(1)
PY
    ); then
        echo 'Check settings.toml and Python 3.11+ before reinstalling.' >&2
        exit 1
    fi
    if [[ -n "$shell_choice" && "$shell_choice" != "$saved_shell" ]]; then
        printf 'Keeping saved shell %s; --shell only applies to fresh installs.\n' "$saved_shell"
        printf 'To change it, edit shell in %s/settings.toml first.\n' "$config"
    fi
    shell_choice="$saved_shell"
    printf 'Using existing Livepanel shell: %s\n' "$shell_choice"
elif [[ -z "$shell_choice" ]]; then
    # SHELL describes the user's preferred shell, unlike this script's Bash.
    detected_shell="${SHELL:-}"
    if [[ -z "$detected_shell" ]] && command -v getent >/dev/null; then
        account_entry=$(getent passwd "$(id -u)" || true)
        detected_shell="${account_entry##*:}"
    fi
    detected_shell="${detected_shell##*/}"
    case "$detected_shell" in
        fish|bash|zsh) shell_choice="$detected_shell";;
        *) shell_choice=bash
           echo 'No supported preferred shell detected; defaulting to Bash.';;
    esac
    if [[ -t 0 ]] && (( ! dry )); then
        printf '\nChoose the shell to use inside Livepanel. Your login shell will not change.\n'
        while true; do
            printf 'Shell (fish/bash/zsh) [%s]: ' "$shell_choice"
            if ! IFS= read -r answer; then
                printf '\nInstallation cancelled.\n' >&2
                exit 1
            fi
            answer="${answer:-$shell_choice}"
            case "$answer" in
                fish|bash|zsh) shell_choice="$answer"; break;;
                *) echo 'Please enter fish, bash or zsh, or press Enter for the default.';;
            esac
        done
    fi
fi
printf 'Selected shell: %s (system login shell unchanged)\n' "$shell_choice"
if [[ -f "$config/settings.toml" ]]; then
    echo 'Keeping the weather location saved in settings.toml.'
    if [[ -n "$location" ]]; then
        echo '--location only applies to fresh installs; edit weather.location in settings.toml to change it.'
    fi
elif [[ -z "$location" ]]; then
    location='London,GB'
    if [[ -t 0 ]] && (( ! dry )); then
        printf '\nWeather location: enter a city and two-letter country code.\n'
        printf 'Examples: Antwerp,BE or Bergen op Zoom,NL. No street address needed.\n'
        while true; do
            printf 'Weather location [%s]: ' "$location"
            if ! IFS= read -r answer; then
                printf '\nInstallation cancelled.\n' >&2
                exit 1
            fi
            answer="${answer:-$location}"
            if [[ "$answer" =~ ^[^,]*[^,[:space:]][[:space:]]*,[[:space:]]*([[:alpha:]]{2})[[:space:]]*$ ]]; then
                country="${BASH_REMATCH[1]}"
                city="${answer%,*}"
                city="${city#"${city%%[![:space:]]*}"}"
                city="${city%"${city##*[![:space:]]}"}"
                location="$city,${country^^}"
                break
            fi
            echo 'Use City,CC, for example Antwerp,BE, or press Enter for London,GB.'
        done
    fi
fi
if [[ ! -f "$config/settings.toml" ]]; then
    printf 'Weather location: %s\n' "$location"
fi
printf 'Livepanel AIO will use:\n  App: %s\n  Config: %s\n  Command: %s/livepanel-aio\n' "$app" "$config" "$bindir"
if ((dry)); then
    printf 'Dependencies: %s; font: %s; autostart: %s; shell: %s\nNo changes made.\n' "$deps" "$font" "$autostart" "$shell_choice"
    exit 0
fi
if ((deps)); then
    elevate=()
    if ((EUID!=0)); then elevate=(sudo); fi
    if command -v pacman >/dev/null; then
        "${elevate[@]}" pacman -S --needed --noconfirm python python-pip tmux "$shell_choice" fastfetch starship playerctl jq bc curl fontconfig librsvg kitty
        if pacman -Si tuptime >/dev/null 2>&1; then "${elevate[@]}" pacman -S --needed --noconfirm tuptime; fi
    elif command -v apt-get >/dev/null; then
        "${elevate[@]}" apt-get update
        "${elevate[@]}" apt-get install -y python3 python3-venv python3-pip tmux "$shell_choice" playerctl jq bc curl fontconfig librsvg2-bin kitty
        # Availability depends on distro release; fallbacks below cover fetch/prompt/weather.
        for package in fastfetch starship ansiweather tuptime; do
            if apt-cache show "$package" >/dev/null 2>&1; then "${elevate[@]}" apt-get install -y "$package"; fi
        done
    elif command -v dnf >/dev/null; then
        "${elevate[@]}" dnf install -y python3 python3-pip tmux "$shell_choice" fastfetch starship playerctl jq bc curl fontconfig librsvg2-tools kitty
        if dnf info tuptime >/dev/null 2>&1; then "${elevate[@]}" dnf install -y tuptime; fi
    else
        echo 'Automatic system dependency installation supports Arch/CachyOS, Debian/Ubuntu and Fedora.' >&2
        echo 'Install the dependencies in docs/install.md, then use --no-deps.' >&2
        exit 1
    fi
fi
command -v python3 >/dev/null || { echo 'Python 3.11+ is required.' >&2; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ is required"'
export LIVEPANEL_INSTALL_SOURCE="$src" LIVEPANEL_INSTALL_APP="$app" LIVEPANEL_CONFIG_DIR="$config" LIVEPANEL_BIN_DIR="$bindir"
export LIVEPANEL_INSTALL_SHELL="$shell_choice" LIVEPANEL_INSTALL_LOCATION="$location"
export LIVEPANEL_INSTALL_DEPS="$deps" LIVEPANEL_INSTALL_FONT="$font" LIVEPANEL_INSTALL_AUTOSTART="$autostart"
python3 "$src/app/install.py"
