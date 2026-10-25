# Customization

All paths below are inside `~/.config/livepanel-aio/`. Restart Livepanel after changes. Run `~/.local/bin/livepanel-aio doctor` to check parsing and dependency paths.

## Shared theme

Change `colors` in `theme.jsonc` to update the dynamic helper, default static preset and default Starship palette together. `label` and `value` are background fills, including borders; `border` sets the border foreground. `divider` sets the tmux divider color. `label_width` and `group_gap` affect the dynamic metric groups only. Static geometry is expressed in its native Fastfetch format strings.

The optional `@theme.name` tokens expand before Fastfetch runs. For example, `{#@theme.green}` uses the shared green foreground; `@theme.label_bg` is a background escape sequence. These are Livepanel extensions: native Fastfetch alone cannot expand them. Configs without these tokens pass through unchanged, apart from resolving the opt-in `@logos/` prefix.

External Fastfetch/Starship configs keep their own colors unless you adapt them to this theme. No engine can automatically restyle every arbitrary config safely.

## Dynamic panel

`dynamic.jsonc` is a real Fastfetch JSONC document. Add, remove or reorder native modules in `modules` exactly as in Fastfetch. Commands run every refresh: use quick, read-only commands. Configured commands execute as your user, so only use dotfiles you trust.

The default has two `command` modules and a `break` between them. Their quoted commands call `render.py` using environment variables supplied by Livepanel. In `columns` mode, each quoted argument defines one group:

```text
'Time=time,Uptime=uptime,OS Age=age,Odometer=odometer,Average=average'
```

The left side of `=` is your title, the right side is a cached metric. Change titles, order or group membership there. Available metrics: `time`, `date`, `uptime`, `age`, `odometer`, `average`, `cpu`, `gpu`, `memory`, `vram`, `swap`, `down`, `up`, `ip`, `processes`, `weather_hint` (legacy compatibility).

The `rows playing weather forecast` command creates the full-width lower box. You can reorder or omit those rows. Long media/weather values use an ellipsis rather than breaking the border. Increase terminal width to see more. Below 95 columns the three metric groups stack; enough terminal height is then needed.

Use native text/ASCII modules in this pane. Put image logos in the static pane: continually redrawing graphics can leave pinned or duplicated images.

## Static Fastfetch and the small FFF

Edit `static.jsonc` like any Fastfetch config: modules, keys, format strings, display options and logo settings are native. This preset omits uptime, RAM usage, network, music and weather already shown above. Hardware model names remain useful static information.

The boxed static preset targets wide terminals. For a narrow terminal, set `static_config = "basic.jsonc"` in `settings.toml`, or provide your own narrower preset. The included static border strings have a fixed 80-cell value area; changing its width requires updating the border lines, padding and cursor-back count together. Very long hardware names may exceed it.

Fastfetch documentation: https://github.com/fastfetch-cli/fastfetch/wiki/Configuration

## Your logo

1. Put your SVG or PNG in `logos/`, for example `logos/my-distro.svg`.
2. In `static.jsonc`, change `logo.source` to `"@logos/my-distro.svg"`.
3. Keep `logo.type = "auto"` and restart.

On Ghostty/Kitty with `kitten` available, auto mode uses `kitty-icat`; SVGs are converted to temporary PNGs with `rsvg-convert`. Elsewhere it uses the bundled LIVE PANEL ASCII fallback. To use your own ASCII file, set `type` to `"file"` and source to `"@logos/my-logo.txt"`. Auto mode also recognizes `.txt`, `.asc` and `.ascii` sources as text. Image-only width/height settings are removed in text mode. The image fallback uses your config folder's `logos/live-panel.txt` when present.

The image dimensions are native Fastfetch `width`/`height` in terminal cells; padding controls spacing. Use absolute image paths in external Fastfetch configs. `@logos/` is the convenient Livepanel-only prefix.

Inside tmux, prefer `kitty-icat` over `kitty-direct`: the latter can remain pinned while text scrolls. If your terminal's image protocol is unreliable, use ASCII. Do not place your image in both shell startup and this preset.

## Prompt

`prompt.toml` is native Starship configuration. The default uses white separators, matching backgrounds and the shared `livepanel` palette. Python is disabled. Copy any Starship preset here to replace it; your global `~/.config/starship.toml` is untouched.

CachyOS uses the custom U+F7000 glyph in the bundled font; other systems retain their Nerd Font OS icons. Change `[os.symbols]` to customize them.

Documentation: https://starship.rs/config/

## Weather, media and odometer

Set `weather.location` in `settings.toml` to `City,CC`, with country code. A commented example is provided. Set `enabled = false` to hide weather. `refresh_seconds = 0` fetches once per session; `900` refreshes every 15 minutes. `Ctrl+b w` refreshes manually. Weather makes requests to ANSIWeather's provider; failures keep the last valid reading and display a status note. Add your own `api_key` in `ansiweather.conf` if the provider requires it; never commit the key.

`media.player = ""` selects an active MPRIS player automatically. Set a player name such as `spotify` to prefer it. Check available names with `playerctl --list-all`. Browser media depends on the browser exposing MPRIS.

Odometer and average use `tuptime` when installed and recording. The installer tries to install it where available; otherwise these fields show unavailable. Its system service/database tracks uptime, not Livepanel. `baseline_seconds` optionally adds historical uptime. OS age uses the root filesystem creation time, which is not necessarily the exact OS installation date.
