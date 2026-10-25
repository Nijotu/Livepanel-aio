# Terminal support and troubleshooting

Livepanel is for Linux terminals with Unicode, ANSI colors and tmux support. It is not a native Windows or macOS application. A Nerd Font is needed for the default prompt icons; true color gives the intended palette.

| Terminal | Default behavior / limitation |
| --- | --- |
| Ghostty | Reference terminal for the original personal build; AIO selects `kitty-icat` image mode when `kitten` is installed. |
| Kitty | AIO selects `kitty-icat`; image behavior still depends on tmux and installed versions. |
| Konsole, GNOME Terminal, Alacritty, WezTerm, VS Code terminal | AIO defaults to ASCII. Some support other image protocols, but those are not auto-selected or verified by this build. |
| Linux virtual console / `TERM=dumb` | Not a supported visual target: fonts, colors or tmux capabilities are insufficient for the intended appearance. |

The earlier AIO SVG scrolling path was confirmed by the user in Ghostty; this refresh still needs an end-to-end check on your terminal. A pseudo-terminal cannot verify graphical placement. For persistent/duplicate images, exit Livepanel and run `kitten icat --clear-all` in the outer terminal, remove duplicate startup fetch calls, and relaunch. Use `logo.type = "file"` for a reliable ASCII fallback. The default SVG is converted using librsvg; your terminal does not need to parse SVG itself.

The static boxed layout is wide. Aim for about 209×65 cells to match the reference. Dynamic groups stack below 95 columns and may need more vertical space. Auto height preserves at least eight shell rows; if the terminal cannot fit your modules, enlarge it or zoom the shell with `Ctrl+b z`.

Mouse capture is enabled by default for output scrolling. tmux owns selection and right-click while enabled, including copying selections to its buffer on release. Terminal mouse-bypass modifiers (often Shift) depend on the terminal. Set `mouse = false` and restart for native mouse handling, using `Ctrl+b [` for output scrollback instead.

## Common fixes

- **Command not found:** use `~/.local/bin/livepanel-aio`, or add `~/.local/bin` to PATH.
- **Config error:** run `~/.local/bin/livepanel-aio doctor`. It checks parsing, not every Fastfetch module option; native Fastfetch errors appear in the panel.
- **Weather missing:** try `ansiweather -l 'London,GB' -u metric -s true -a false`. Verify network/provider credentials; the bundled API default is not guaranteed to remain available.
- **Nothing playing:** run `playerctl --list-all`; the app must expose MPRIS on your desktop session bus.
- **GPU readings unavailable:** supported AMD sysfs files or NVIDIA's driver tools are required. Intel GPU utilization is not implemented.
- **OS age unavailable:** the root filesystem did not report a creation timestamp.
- **Odometer unavailable:** install/enable your distribution's tuptime tracking; it cannot reconstruct uptime from before recording began.
- **Right-click shows tmux's menu:** ensure `mouse = false` in settings and restart the AIO session.
- **Two fetch displays:** your shell rc may also run an older fetch. Disable that startup call if needed; Livepanel loads your normal shell config before its own static fetch and prompt.
- **Nested session:** launch from a regular terminal outside tmux. Livepanel creates its own isolated tmux server.

Exit using `exit`. `Ctrl+b d` detaches the tmux client; it does not stop the session. To find a detached session, read its `socket` in `~/.cache/livepanel-aio/sessions/*/session.json`, then use `tmux -L SOCKET attach -t livepanel`. Closing the last shell pane stops that AIO server.
