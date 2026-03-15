# WayMakeup

WayMakeup is a regular Ubuntu desktop app that opens a transparent drawing window. You can use it to sketch arrows, rectangles, circles, and text on top of your desktop view, then capture the result with the built-in screenshot tool.

## Features

- Transparent drawing window
- Fullscreen on launch
- Arrow, rectangle, circle, and text tools
- Undo and clear
- Movable toolbar with collapse and auto-avoid behavior
- Multiline text editor with live placement preview

## Run

Install the GTK/Cairo Python bindings first:

```bash
sudo apt install python3-gi python3-cairo python3-gi-cairo gir1.2-gtk-4.0 gir1.2-pango-1.0
```

Then launch the app:

```bash
python3 app.py
```

## Website

A static showcase page is included in `site/`. You can host it with Nginx on Azure or any static web server.

- Landing page: `site/index.html`
- Styles: `site/styles.css`
- Sample Nginx config: `site/nginx.conf`
- Local Docker preview: `docker-compose.yml`
- Download archive target: `site/downloads/wymakeup-source.zip`

### Test the website locally with Docker

Once Docker and Docker Compose are installed:

```bash
docker compose up --build
```

Then open `http://localhost:8080`.

## Publish a Release

GitHub Actions can package the desktop app and upload it to GitHub Releases when you push a version tag.

```bash
git add .
git commit -m "Prepare release"
git tag v1.0.1
git push origin main
git push origin v1.0.1
```

That workflow uploads these release assets:

- `wymakeup-vX.Y.Z.zip`
- `wymakeup-vX.Y.Z.tar.gz`
- `SHA256SUMS.txt`

## Install launcher

Copy `WayMakeup.desktop` into `~/.local/share/applications/` if you want it to show up in the Ubuntu app launcher.

```bash
mkdir -p ~/.local/share/applications
cp /home/seb/Code/GitHub/wymakeup/WayMakeup.desktop ~/.local/share/applications/
```

## Shortcuts

- `Ctrl+Z`: undo
- `Delete`: clear all
- `Esc`: quit

## Notes

- This is a normal Wayland app window, not a compositor overlay.
- You can see what is behind the window, but while the window is focused your input goes to WayMakeup.
- If your theme or compositor renders transparency differently, you may want to keep the app slightly smaller than fullscreen or adjust the CSS in `app.py`.
