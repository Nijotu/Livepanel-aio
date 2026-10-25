# Livepanel AIO

Live system information above a normal terminal shell, with matching static system information and a Starship prompt. Run your usual commands while the top panel updates.

One installer sets up the application, Fastfetch, Starship, ANSIWeather, playerctl and the bundled Nerd Font. It uses your real system readings, a neutral London weather default and a replaceable LIVE PANEL logo.

## Install and run

Extract this folder, open a terminal in it, then run **as your normal user**:

```sh
bash install.sh
~/.local/bin/livepanel-aio
```

On a fresh interactive install, the installer detects your preferred shell and offers Fish, Bash or Zsh. Press Enter to accept the suggested shell, or type another choice. If detection fails, Bash is suggested. This selects the shell inside Livepanel; it does not change your system login shell.

The installer asks for sudo through your package manager when needed. Internet access is required. Automatic dependencies support Arch/CachyOS, Debian/Ubuntu and Fedora; Python 3.11+ is required.

Select **DroidSansMono Cachy Nerd Font** in your terminal's font settings, then open a new terminal window. In Ghostty, add this to `~/.config/ghostty/config`:

```ini
font-family = DroidSansMono Cachy Nerd Font
font-size = 10
```

### Choose Bash, Zsh or Fish explicitly

Use one of these commands to skip the shell-selection question on a fresh install:

| Shell | Install command |
| --- | --- |
| Bash | `bash install.sh --shell bash` |
| Zsh | `bash install.sh --shell zsh` |
| Fish | `bash install.sh --shell fish` |

The installer itself runs with Bash for all three choices. It installs the selected shell if needed when automatic dependency installation is enabled, and Livepanel initialises its Starship prompt for that shell. You do not need to configure Starship separately for Livepanel.

After installation, start any of them with `~/.local/bin/livepanel-aio`. Without an interactive terminal, the installer uses the detected shell without prompting; use `--shell` for a predictable scripted install.

**Reinstalling preserves your existing shell choice.** To change it permanently, edit `shell = "bash"`, `shell = "zsh"` or `shell = "fish"` in `~/.config/livepanel-aio/settings.toml`. The installer's `--shell` option only sets up new configurations.

Fresh interactive installs also ask for your weather city and two-letter country code, for example `Antwerp,BE`. Press Enter to keep `London,GB`. The installer saves this in `settings.toml`, and Livepanel passes it to ANSIWeather for current weather and forecasts.

To skip the weather question during a first install:

```sh
bash install.sh --location 'Paris,FR'
```

Reinstalls keep your saved location. Noninteractive installs and dry runs use London unless `--location` is supplied. You can change `weather.location` in `settings.toml` later and restart Livepanel.

## Updating an existing installation

Run `bash install.sh` from this extracted folder after exiting Livepanel. Your settings are preserved, and updated defaults are saved beside them as `.example` files.

To replace the old **Weather / forecast below** row with **Processes**, open `~/.config/livepanel-aio/dynamic.jsonc`, replace `Weather=weather_hint` with `Processes=processes`, then restart Livepanel. Fresh installs already use Processes. The odometer code fix applies on reinstall without changing your baseline.

## Use it

- Type commands in the lower pane, as usual.
- `Ctrl+b`, then `w`: refresh weather.
- `Ctrl+b`, then `z`: zoom the shell; repeat to restore the panels.
- `Ctrl+b`, then `[`: scrollback/copy mode; press `q` to leave it.
- Type `exit` to close Livepanel and return to the outer shell.

Mouse scrolling is enabled by default through tmux. Dragging selects text and copies it to tmux's buffer on release; right-click opens tmux's menu. For your terminal's native selection/menu, use its mouse-bypass modifier where supported (often Shift), or set `mouse = false` in `settings.toml` and restart. With mouse capture off, use `Ctrl+b`, then `[` to scroll output. The small FFF is a Fastfetch preset, not the unrelated `fff` file manager.

## Customize

Open `~/.config/livepanel-aio/`:

| File | Controls |
| --- | --- |
| `theme.jsonc` | Shared panel and prompt colors; dynamic label widths and gaps |
| `dynamic.jsonc` | Live panel modules and boxed metric groups |
| `static.jsonc` | Small static Fastfetch layout and logo |
| `prompt.toml` | Native Starship prompt; Python is disabled by default |
| `settings.toml` | Shell, weather location, refresh, pane height and static preset |
| `logos/` | Your SVG, PNG or ASCII logo files |

Restart Livepanel after editing. Both panel configs are processed by **real Fastfetch**, so native modules and formatting stay native. The default live boxes use a bundled Fastfetch `command` helper; its metric-group syntax is an additional Livepanel feature. Any Starship TOML config can replace `prompt.toml`.

To plug in an existing Fastfetch file:

```sh
~/.local/bin/livepanel-aio --fastfetch "$HOME/.config/fastfetch/config.jsonc"
```

Or set `static_config` in `settings.toml`. `basic.jsonc` is included as a simple alternative.

## Configure the odometer

**Uptime** measures the current boot. **Odometer** shows accumulated uptime recorded by `tuptime`, plus an optional historical baseline. Livepanel does not reconstruct uptime from before tracking began.

Check whether tracking is available:

```sh
tuptime
```

The installer attempts to install this optional dependency where available. If the command is missing, install `tuptime` using your distribution's package instructions. Upstream lists Debian/Ubuntu and Fedora packages; Arch users may need the AUR if their enabled repositories do not provide it.

On systems using the upstream systemd units, enable startup/shutdown tracking:

```sh
sudo systemctl enable --now tuptime.service
```

If your package supplies `tuptime-sync.timer`, enable periodic database updates too:

```sh
sudo systemctl enable --now tuptime-sync.timer
```

Some packages use cron instead of that timer. Follow your package's setup instructions if the unit is missing; an enabled service may show `active (exited)` normally. See the [upstream tuptime manual](https://github.com/rfmoz/tuptime/blob/master/tuptime-manual.txt) for installation and scheduling details.

### Optional historical uptime

In `~/.config/livepanel-aio/settings.toml`, edit the existing section:

```toml
[odometer]
baseline_seconds = 0
```

Leave this at zero unless you know how much uptime is missing from tuptime's records. For example, **100 unrecorded hours** is `360000` seconds. Add only missing time, not time tuptime already includes. Save and restart Livepanel. This setting changes Livepanel's displayed total, not the tuptime database, and still requires readable tuptime output.

**Average** currently divides the odometer total by the age of the root filesystem. It is an estimate of hours per day across that period, not tuptime's average boot duration. Starting tracking on an older installation can therefore produce a low average. Without a filesystem creation timestamp, Average is unavailable.

### Counters missing or unexpectedly zero

Compare these reports:

```sh
tuptime
env LC_ALL=C tuptime -sn
```

Odometer displays whole hours, so less than an hour can correctly show `0 h`. This build fixes the earlier bug that read tuptime's percentage instead of its seconds. If readings still disagree, check that tuptime succeeds as your normal user and that `baseline_seconds` includes only missing historical uptime. Do not use a baseline to compensate for a reporting error.

## Open automatically

To enable autostart for an existing installation, rerun the installer from the extracted project folder:

```sh
bash install.sh --autostart
```

The installer uses the shell already saved in `settings.toml`; you do not need to repeat `--shell`.

For a **fresh installation with autostart**, choose one:

| Shell | Install and enable autostart |
| --- | --- |
| Bash | `bash install.sh --shell bash --autostart` |
| Zsh | `bash install.sh --shell zsh --autostart` |
| Fish | `bash install.sh --shell fish --autostart` |

This adds a guarded startup hook to `.bashrc`, `.zshrc` (respecting `ZDOTDIR`), or Fish's `conf.d` folder. It skips SSH, existing tmux sessions and shells inside Livepanel. Existing configs are preserved on reinstall. Disable any older Livepanel autostart yourself first.

Your terminal must launch the selected shell for its hook to run. For example, adding a Zsh hook does not change a terminal that currently opens Fish. Bash autostart requires the terminal's startup sequence to read `.bashrc`; login-shell setups may need their profile to source it.

## Trying this alongside an older Livepanel

This build uses the separate name **livepanel-aio** and its own folders. It does not replace `livepanel`, `fff`, your old config folders or your global Starship config. Leave `--autostart` off while testing.

[Installation, font setup and removal](docs/install.md) · [Customization and logos](docs/customize.md) · [Terminal support and troubleshooting](docs/compatibility.md)

## Reference appearance

The original personal setup used CachyOS, Fish and Ghostty with the supplied font. For a similar layout, use a wide terminal (about 209 columns × 65 rows). Optional Ghostty settings:

```ini
background-opacity = 0.8
window-width = 209
window-height = 65
font-size = 10
font-family = DroidSansMono Cachy Nerd Font
```

Other setups can use the same panels; fonts, image support, terminal size and transparency affect the result. The wallpaper and desktop theme belong to your terminal/desktop settings.

This is an AIO test build, developed with AI assistance. See [validation notes](docs/validation.md) for what was actually tested. Project code is MIT licensed; bundled font and third-party components retain their own licenses.
