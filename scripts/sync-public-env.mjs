import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const rootDir = process.cwd();
const envPath = path.join(rootDir, ".env");
const outputPath = path.join(rootDir, "src", "config", "public-env.generated.js");

export function parseEnvContents(contents) {
  const values = {};
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

export function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  return parseEnvContents(fs.readFileSync(filePath, "utf8"));
}

function toJsString(value) {
  return JSON.stringify(value ?? "");
}

export function resolvePublicEnv({ fileValues = {}, processValues = process.env } = {}) {
  return {
    supabaseUrl: processValues.SUPABASE_URL ?? fileValues.SUPABASE_URL ?? "",
    supabaseAnonKey: processValues.SUPABASE_ANON_KEY ?? fileValues.SUPABASE_ANON_KEY ?? ""
  };
}

export function getMissingPublicEnvKeys(publicEnv) {
  const missing = [];
  if (!publicEnv.supabaseUrl) {
    missing.push("SUPABASE_URL");
  }
  if (!publicEnv.supabaseAnonKey) {
    missing.push("SUPABASE_ANON_KEY");
  }
  return missing;
}

export function renderPublicEnvScript(publicEnv) {
  return `window.__SUPABASE_URL__ = ${toJsString(publicEnv.supabaseUrl)};\nwindow.__SUPABASE_ANON_KEY__ = ${toJsString(publicEnv.supabaseAnonKey)};\n`;
}

export function writePublicEnvFile({ strict = false, filePath = envPath, processValues = process.env } = {}) {
  const fileValues = parseEnvFile(filePath);
  const publicEnv = resolvePublicEnv({ fileValues, processValues });
  const missingKeys = getMissingPublicEnvKeys(publicEnv);
  if (strict && missingKeys.length > 0) {
    throw new Error(`Missing required public env: ${missingKeys.join(", ")}`);
  }

  fs.writeFileSync(outputPath, renderPublicEnvScript(publicEnv), "utf8");
  return { outputPath, missingKeys };
}

const entrypoint = process.argv[1] ? pathToFileURL(process.argv[1]).href : "";
if (import.meta.url === entrypoint) {
  const strict = process.argv.includes("--strict");

  try {
    const { outputPath: writtenPath, missingKeys } = writePublicEnvFile({ strict });
    if (!strict && missingKeys.length > 0) {
      console.warn(`Warning: missing public env keys: ${missingKeys.join(", ")}`);
    }
    console.log(`Wrote ${path.relative(rootDir, writtenPath)}`);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
