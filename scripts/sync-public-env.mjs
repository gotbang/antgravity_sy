import fs from "node:fs";
import path from "node:path";

const rootDir = process.cwd();
const envPath = path.join(rootDir, ".env");
const outputPath = path.join(rootDir, "src", "config", "public-env.generated.js");

function parseEnvFile(filePath) {
  const values = {};
  if (!fs.existsSync(filePath)) {
    return values;
  }

  const contents = fs.readFileSync(filePath, "utf8");
  for (const line of contents.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) {
      continue;
    }

    const [rawKey, ...rawValueParts] = trimmed.split("=");
    const key = rawKey.trim();
    const value = rawValueParts.join("=").trim();
    values[key] = value;
  }

  return values;
}

function toJsString(value) {
  return JSON.stringify(value ?? "");
}

const env = parseEnvFile(envPath);
const contents = `window.__SUPABASE_URL__ = ${toJsString(env.SUPABASE_URL)};\nwindow.__SUPABASE_ANON_KEY__ = ${toJsString(env.SUPABASE_ANON_KEY)};\n`;

fs.writeFileSync(outputPath, contents, "utf8");
console.log(`Wrote ${path.relative(rootDir, outputPath)}`);
