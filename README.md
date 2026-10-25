# Livepanel AIO

Live system information above a normal terminal shell, with matching static system information and a Starship prompt. Run your usual commands while the top panel updates.

One installer sets up the application, Fastfetch, Starship, ANSIWeather, playerctl and the bundled Nerd Font. It uses your real system readings, a neutral London weather default and a replaceable LIVE PANEL logo.

## Quick start

Download and extract the project ZIP. Open a terminal **inside the extracted folder containing `install.sh`**, then run as your normal user:

```sh
bash install.sh
```

On a fresh install, choose your shell (Fish, Bash or Zsh) and weather location (`City,CC`). Press Enter to accept the detected shell and `London,GB`. The installer does not change your system login shell. It requests sudo for system packages when needed; do not run the entire installer with sudo.

Select **DroidSansMono Cachy Nerd Font** in your terminal's font settings. Open a new terminal and launch:

```sh
~/.local/bin/livepanel-aio
```

You can launch Livepanel from any folder. You do not need to keep the extracted download after installation, although you will need an extracted source copy to reinstall or update.

Internet access and Python 3.11+ are required. Automatic dependency installation supports pacman, apt and dnf systems, including CachyOS/Arch, Debian/Ubuntu and Fedora. This is installer support, not a claim that every distribution has been tested. See [detailed requirements](docs/install.md).

**Mouse behaviour:** scrolling is enabled through tmux. Selection and right-click therefore use tmux's behaviour; see [controls](#controls-and-mouse-behaviour) below.

## Which folder do I use?

| Task | Location or command |
| --- | --- |
| Install, update or enable autostart | Run `bash install.sh` with any options from the extracted project folder |
| Launch from anywhere | `~/.local/bin/livepanel-aio` |
| Edit settings, panels, prompt or logos | `~/.config/livepanel-aio/` |
| Installed application files | `~/.local/share/livepanel-aio/` |
| Uninstall from anywhere | `bash ~/.local/share/livepanel-aio/uninstall.sh` |

These are the default paths; custom XDG or installer paths can change them. The config folder contains settings, not the installer. The downloaded uninstaller cannot remove an installation by itself: use the installed copy, which has the installation record.

## Shell and weather options

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

## Controls and mouse behaviour

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

## Font and logo

The installer copies the bundled font and refreshes the font cache unless you use `--no-font`. You still need to select the font in your terminal. In Ghostty, add this to `~/.config/ghostty/config`, then reopen the terminal:

```ini
font-family = DroidSansMono Cachy Nerd Font
font-size = 10
```

Other terminals: open your profile or appearance settings and select **DroidSansMono Cachy Nerd Font**. See [font instructions for other terminals](docs/install.md#font-selection). The custom CachyOS prompt glyph requires the bundled font.

To replace the LIVE PANEL logo, put your image in `~/.config/livepanel-aio/logos/` and update the existing `logo` section in `static.jsonc`:

```jsonc
"type": "auto",
"source": "@logos/my-logo.svg"
```

Auto mode selects image rendering on Ghostty/Kitty when the image helper is available; other terminals use the text fallback. For a text logo, use `"type": "file"` and a source such as `"@logos/live-panel.txt"`. Auto mode also recognizes `.txt`, `.asc` and `.ascii` filenames. Restart Livepanel after changing the logo. See [logo customization](docs/customize.md#your-logo) for details.

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

## Uninstall

Exit Livepanel first. From any terminal directory, run the **installed** uninstaller:

```sh
bash ~/.local/share/livepanel-aio/uninstall.sh
```

It removes the application, its launcher and its recorded startup hooks. Other shell settings are retained. Your Livepanel configs, installed system dependencies and font are kept.

To remove the Livepanel config folder too, add `--purge-config`:

```sh
bash ~/.local/share/livepanel-aio/uninstall.sh --purge-config
```

This deletes your Livepanel customizations. Export or back them up first if you want to keep them. Timestamped application backups are not automatically removed.

## Starting directory and troubleshooting

Livepanel starts its shell in the directory it was launched from. If you move an extracted folder to Trash while a terminal is still inside it, a later launch from that terminal may start in the Trash folder too.

Type `exit` to leave Livepanel, then run these in the **outer shell**:

```sh
cd ~
~/.local/bin/livepanel-aio
```

Changing directory only inside Livepanel does not change the outer shell's directory. For an autostarted terminal that still opens somewhere unexpected, check the terminal's configured working directory.

For config and dependency diagnostics:

```sh
~/.local/bin/livepanel-aio doctor
```

Run Livepanel from a normal terminal outside an existing tmux session. For more fixes, see [troubleshooting](docs/compatibility.md).

## Known limitations and testing

- The static boxed preset has fixed-width value fields and is intended for a wide terminal. About 209 columns × 65 rows matches the reference; very long values may exceed the border. Use `static_config = "basic.jsonc"` or a narrower custom Fastfetch preset for smaller windows.
- Dynamic metric groups stack at narrow widths. If the screen cannot fit everything, enlarge it or use `Ctrl+b`, then `z` to zoom the shell.
- Image rendering depends on terminal support and installed versions. The text logo is the fallback. This is a Linux application; native Windows and macOS are not supported targets.
- Weather requires network access and a working provider configuration. Media information requires an application that exposes MPRIS. GPU and temperature readings depend on supported hardware and drivers.
- Mouse selection and menus follow tmux while mouse capture is enabled. Native terminal mouse behaviour is not guaranteed without a bypass modifier or disabling capture.

The maintainer has tested a fresh app/config installation on an existing CachyOS system with Fish and Ghostty, including the corrected odometer and Processes row. Upgrade preservation, uninstall cleanup, terminal resizing and long command output have also been checked by the maintainer. The current build passed 13 automated core tests.

**A clean-VM installation without preinstalled dependencies is still pending.** Earlier shell-only checks covered Bash and Zsh, but do not establish full graphical or cross-distribution coverage. This is a beta candidate; see [validation details](docs/validation.md) for test scope.

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

## Credits and licence

Livepanel AIO was developed with AI assistance. It uses Fastfetch, Starship, tmux, ANSIWeather, playerctl and other open-source components. The small FFF is a Fastfetch preset, not the unrelated `fff` file manager.

Project code is [MIT licensed](LICENSE). Bundled font and third-party components retain their own licences; see [third-party notes](docs/third-party.md) and [font credits](fonts/README.md).
