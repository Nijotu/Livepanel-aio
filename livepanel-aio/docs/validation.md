# Validation

## October 25 revision 2

Based on the latest user-supplied source and configuration comparison. The source copies have identical application files; the edited copy places the 100-file example folder inside the project. That folder is retained for manual scrolling checks and is not installed as application data. The only active-config difference was a personal weather city; public defaults remain London and reinstalls preserve the user's configured city.

This revision replaces the redundant forecast hint with a live process count, fixes percentage-prefixed tuptime seconds parsing, and clears stale odometer values when tuptime fails. The legacy weather_hint metric remains available for existing configs. See README for the one-line config change needed on upgrades.

13 automated tests passed for this revision, including process collection, realistic percentage-prefixed tuptime reports, historical baseline arithmetic, and failed-read handling. Config parsing and shell syntax checks also passed. A fresh graphical-terminal installation was not repeated here.

## October 25 refresh

This build combines the supplied tested source and active configuration. The supplied launchers were identical and contained machine-specific paths, so they are not distributed; the installer generates the correct launcher for each user. Updated shell selection and README instructions are included. Mouse capture is enabled, the SVG is the default, and the diagonal text fallback and CachyOS font glyph are retained. A duplicate root-level font was removed; the licensed copy remains in `fonts/`.

Logo auto mode now recognizes text filenames and uses the configured text fallback. Text mode discards image width/height hints. All 11 core tests passed for this refresh, including new regressions for these cases. Python/TOML parsing, shell syntax checks and installer dry runs for Bash, Zsh and Fish also passed. The shell-selection update previously passed 11 checks. The added fresh-install weather prompt passed eight checks covering default/custom locations, format retry, country-code normalization, noninteractive defaults, explicit overrides and preservation of existing settings.

This refresh does not claim a new full GUI or package-manager installation test. Existing user configs are preserved on reinstall, so merged defaults are written as `.example` files instead of replacing customized settings.

## Earlier build validation

Verified in the earlier isolated Linux environment:

- Fresh user-local installation using existing system dependencies (`--no-deps --no-font`), with a separate Python venv.
- Reinstallation preserves customized settings and writes new defaults as `.example` files.
- Managed Bash autostart insertion and uninstall removal; unrelated rc content and retained configs survive.
- Nine automated tests covering rendering widths/fills, config passthrough, theme expansion, height measurement, weather parsing, metadata sanitization, missing media tooling and uptime parsing.
- Real Fastfetch 2.70.0 rendering of both configs, including a 209-cell dynamic frame with a blank line between groups and footer.
- Real Starship 1.26.0 prompt rendering.
- Fish 3.7, Bash and Zsh 5.9 startup with the static fetch and Starship, command execution and exit in pseudo-terminals. The tmux-client readiness check was substituted for these shell-only tests.
- SVG conversion with librsvg and font-family metadata inspection.

Not verified here: full tmux pane lifecycle, Ghostty image placement/scrolling, desktop MPRIS playback, hardware sensor readings on a physical PC, or every distro's package-manager installation. The test environment denies Unix sockets, so tmux cannot start its server. No claim of an end-to-end graphical-terminal pass is made.

Try the AIO alongside your existing setup first. Use `exit` to close it. Check panel resizing, the logo scrolling with static text, music/weather and native right-click in your own terminal before enabling autostart.

To rerun unit tests from the source folder after installing the Python requirements:

```sh
python3 -m unittest discover -s tests -v
```
