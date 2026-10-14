/**
 * Side-effect import: fills missing process.env keys from the LifeOS .env files,
 * so FRED_API_KEY / EIA_API_KEY work without the caller exporting them.
 *
 * Search order (first file wins per key; real environment variables always win):
 *   $LIFEOS_CONFIG_DIR/.env → ~/.config/LifeOS/.env → $LIFEOS_DIR/.env (default ~/.claude/.env)
 *
 * Parsed line by line rather than shell-sourced, so an unquoted value with a space
 * elsewhere in the file does not break key loading.
 */
import { readFileSync } from "fs";
import { homedir } from "os";
import { join } from "path";

const candidates = [
  process.env.LIFEOS_CONFIG_DIR && join(process.env.LIFEOS_CONFIG_DIR, ".env"),
  join(homedir(), ".config", "LifeOS", ".env"),
  join(process.env.LIFEOS_DIR || join(homedir(), ".claude"), ".env"),
].filter(Boolean) as string[];

for (const envPath of candidates) {
  let content: string;
  try {
    content = readFileSync(envPath, "utf-8");
  } catch {
    continue;
  }
  for (const line of content.split("\n")) {
    const match = line.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$/);
    if (!match) continue;
    const [, key, raw] = match;
    if (process.env[key] !== undefined) continue;
    let value = raw.trim();
    const quoted = value.match(/^(["'])(.*)\1/);
    // Quoted values keep everything inside the quotes; unquoted ones drop a trailing " # comment".
    value = quoted ? quoted[2] : value.replace(/\s+#.*$/, "");
    process.env[key] = value;
  }
}
