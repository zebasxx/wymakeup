# WayMarkup

WayMarkup is a regular Ubuntu desktop app that opens a transparent drawing window. You can use it to sketch arrows, rectangles, circles, and text on top of your desktop view, then capture the result with the built-in screenshot tool.

## Features

- Transparent drawing window
- Fullscreen on launch
- Arrow, rectangle, circle, and text tools
- Undo, clear, and fullscreen toggle
- Small floating toolbar

## Run

```bash
python3 app.py
```

## Install launcher

Copy `waymarkup.desktop` into `~/.local/share/applications/` if you want it to show up in the Ubuntu app launcher.

```bash
mkdir -p ~/.local/share/applications
cp /home/seb/Code/GitHub/wymakeup/waymarkup.desktop ~/.local/share/applications/
```

## Shortcuts

- `Ctrl+Z`: undo
- `Delete`: clear all
- `F11`: toggle fullscreen
- `Esc`: quit

## Notes

- This is a normal Wayland app window, not a compositor overlay.
- You can see what is behind the window, but while the window is focused your input goes to WayMarkup.
- If your theme or compositor renders transparency differently, you may want to keep the app slightly smaller than fullscreen or adjust the CSS in `app.py`.
