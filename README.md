# DBR RP roster

Local roster website for a Roblox roleplay faction. Staff records are stored in `dbr.sqlite3` and Roblox identities are resolved by username through Roblox's public users API.

## Run on Windows

Open PowerShell in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The server prints a temporary administrator token on startup. Keep that terminal open, visit `http://127.0.0.1:5000/admin`, and paste the token into the access field. The token is generated again after each restart unless `DBR_ADMIN_TOKEN` is set. Anyone with the token can add, edit, and remove staff, so do not share it publicly.

Open `http://127.0.0.1:5000/` for the public site. Add a player with their exact Roblox username, choose their faction rank and department, and optionally enter a call sign. Their Roblox display name and headshot are loaded automatically. The public roster only displays these faction fields and the Roblox profile/avatar links.

The roster API is local-only by default (`127.0.0.1`). To make it available over the internet, deploy it behind HTTPS with a production WSGI server and set a strong `DBR_ADMIN_TOKEN`; do not expose Flask's development server directly.

## Roblox avatars

Headshots use Roblox's public avatar-headshot thumbnail API. The 3D action opens the employee's official Roblox profile in a new tab, where Roblox provides its own interactive avatar viewer. Roblox blocks embedding profile pages and currently rejects anonymous requests to its avatar-3d model endpoint, so the model cannot be rendered inside this site without Roblox changing those access rules.

## GitHub Pages

The workflow in `.github/workflows/pages.yml` builds and deploys a static copy on pushes to `main` or `master`. In the repository's GitHub settings, choose **Pages → Build and deployment → Source: GitHub Actions** once. The build publishes only the public HTML, CSS, JavaScript, logo, and JSON data; it does not publish the Flask admin page, Python backend, or SQLite database.

To publish a news item locally, open `/admin`, sign in with the startup token, and use **Керування новинами** to add or delete publications. Changes are saved to `data/news.json`. You can also edit this JSON file directly. The Pages workflow publishes JSON changes after they are pushed to GitHub.

The JSON format for a publication is:

```json
{
	"date": "2026-09-29",
	"category": "Оголошення",
	"title": "Заголовок новини",
	"summary": "Короткий вступ до новини.",
	"content": ["Основний текст новини.", "За потреби додай наступний абзац."]
}
```

Commit and push the edited JSON file; the workflow will publish the update. News is sorted newest first and can be searched or filtered by category on `news.html`.

For GitHub Pages, the public staff roster comes from `data/staff.json`. Each item needs `roblox_user_id`, `username`, `display_name`, `rank`, and `department`; `call_sign` is optional. The build resolves Roblox headshot URLs and writes the public copy to `_site/data/staff.json`. The local `/admin` panel still writes to SQLite, so copy staff changes into `data/staff.json` before pushing to publish them on Pages.

`build_pages.py` can be run locally with Python to preview the deployment output in `_site`. No GitHub remote or Git executable is configured in this workspace, so publishing requires connecting this folder to the repository and pushing it to GitHub.

## Tests

```powershell
python -m unittest -v
```
