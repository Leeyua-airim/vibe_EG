import json
from pathlib import Path
from django.conf import settings

from core.models import GeneratedApp


def _safe_slug(value: str) -> str:
    value = (value or "generated-app").strip().lower()
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-") or "generated-app"


def _build_package_json(app_name: str) -> str:
    data = {
        "name": app_name,
        "private": True,
        "version": "0.0.1",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1"
        },
        "devDependencies": {
            "@types/react": "^18.3.3",
            "@types/react-dom": "^18.3.0",
            "@vitejs/plugin-react": "^4.3.1",
            "typescript": "^5.5.4",
            "vite": "^5.4.2"
        }
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def _build_index_html(title: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""


def _build_vite_config() -> str:
    return """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
"""


def _build_tsconfig() -> str:
    data = {
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "allowJs": False,
            "skipLibCheck": True,
            "esModuleInterop": True,
            "allowSyntheticDefaultImports": True,
            "strict": True,
            "forceConsistentCasingInFileNames": True,
            "module": "ESNext",
            "moduleResolution": "Node",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx"
        },
        "include": ["src"],
        "references": []
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def _build_main_tsx() -> str:
    return """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""


def _build_app_css() -> str:
    return """body {
  margin: 0;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f7f7fb;
  color: #111827;
}

* {
  box-sizing: border-box;
}

.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 48px 20px;
}

.card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

h1, h2 {
  margin-top: 0;
}

ul {
  padding-left: 20px;
}

.badge {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 9999px;
  background: #eef2ff;
  color: #4338ca;
  font-size: 14px;
  margin-bottom: 12px;
}
"""


def _build_app_tsx(spec: dict) -> str:
    title = spec.get("title", "생성 앱")
    summary = spec.get("summary", "")
    features = spec.get("features", [])
    inputs = spec.get("inputs", [])
    outputs = spec.get("outputs", [])
    ui_pattern = spec.get("ui_pattern", "unknown")

    features_items = "\n".join([f"          <li>{item}</li>" for item in features]) or "          <li>기능 정보 없음</li>"
    inputs_items = "\n".join([f"          <li>{item}</li>" for item in inputs]) or "          <li>입력 정보 없음</li>"
    outputs_items = "\n".join([f"          <li>{item}</li>" for item in outputs]) or "          <li>출력 정보 없음</li>"

    return f"""export default function App() {{
  return (
    <div className="container">
      <div className="card">
        <div className="badge">UI Pattern: {ui_pattern}</div>
        <h1>{title}</h1>
        <p>{summary}</p>
      </div>

      <div className="card">
        <h2>주요 기능</h2>
        <ul>
{features_items}
        </ul>
      </div>

      <div className="card">
        <h2>입력</h2>
        <ul>
{inputs_items}
        </ul>
      </div>

      <div className="card">
        <h2>출력</h2>
        <ul>
{outputs_items}
        </ul>
      </div>
    </div>
  )
}}
"""


def scaffold_generated_app(app: GeneratedApp) -> dict:
    spec = app.spec_json or {}
    if not isinstance(spec, dict):
        raise ValueError("app.spec_json 형식이 올바르지 않습니다.")

    title = spec.get("title") or app.name or "generated-app"
    slug = _safe_slug(title)

    base_dir = Path(settings.BASE_DIR) / "generated_apps"
    project_root = base_dir / f"app_{app.id}_{slug}"
    src_dir = project_root / "src"

    src_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "package.json": _build_package_json(slug),
        "index.html": _build_index_html(title),
        "vite.config.ts": _build_vite_config(),
        "tsconfig.json": _build_tsconfig(),
        "src/main.tsx": _build_main_tsx(),
        "src/App.tsx": _build_app_tsx(spec),
        "src/App.css": _build_app_css(),
    }

    files_created = []

    for relative_path, content in files.items():
        file_path = project_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        files_created.append(relative_path)

    app.project_root = str(project_root)
    app.entry_file = "src/App.tsx"
    app.status = GeneratedApp.Status.GENERATED
    app.save(update_fields=["project_root", "entry_file", "status", "updated_at"])

    return {
        "files_created": files_created,
    }