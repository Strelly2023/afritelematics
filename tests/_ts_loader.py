from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TYPESCRIPT = ROOT / "novapay_consumer_app/node_modules/typescript"


def load_ts_exports(relative_module_path: str) -> dict:
    script = f"""
const Module = require('module');
const fs = require('fs');
const ts = require('{TYPESCRIPT.as_posix()}');
const rootResolve = Module._resolveFilename;
Module._resolveFilename = function(request, parent, isMain, options) {{
  try {{
    return rootResolve.call(this, request, parent, isMain, options);
  }} catch (error) {{
    if (request.startsWith('./') || request.startsWith('../')) {{
      try {{
        return rootResolve.call(this, request + '.ts', parent, isMain, options);
      }} catch (fallbackError) {{
        throw error;
      }}
    }}
    throw error;
  }}
}};
require.extensions['.ts'] = function(module, filename) {{
  const source = fs.readFileSync(filename, 'utf8');
  const result = ts.transpileModule(source, {{
    compilerOptions: {{
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2021,
      esModuleInterop: true
    }}
  }});
  module._compile(result.outputText, filename);
}};
const exported = require('./{relative_module_path}');
console.log(JSON.stringify(exported));
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


def run_ts_query(relative_module_path: str, expression: str) -> object:
    script = f"""
const Module = require('module');
const fs = require('fs');
const ts = require('{TYPESCRIPT.as_posix()}');
const rootResolve = Module._resolveFilename;
Module._resolveFilename = function(request, parent, isMain, options) {{
  try {{
    return rootResolve.call(this, request, parent, isMain, options);
  }} catch (error) {{
    if (request.startsWith('./') || request.startsWith('../')) {{
      try {{
        return rootResolve.call(this, request + '.ts', parent, isMain, options);
      }} catch (fallbackError) {{
        throw error;
      }}
    }}
    throw error;
  }}
}};
require.extensions['.ts'] = function(module, filename) {{
  const source = fs.readFileSync(filename, 'utf8');
  const result = ts.transpileModule(source, {{
    compilerOptions: {{
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2021,
      esModuleInterop: true
    }}
  }});
  module._compile(result.outputText, filename);
}};
const exported = require('./{relative_module_path}');
const value = {expression};
console.log(JSON.stringify(value));
"""
    result = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(result.stdout)
