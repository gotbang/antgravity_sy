import { describe, expect, it } from "vitest";

import {
  getMissingPublicEnvKeys,
  renderPublicEnvScript,
  resolvePublicEnv
} from "../../scripts/sync-public-env.mjs";

describe("sync-public-env", () => {
  it("prefers process env over .env file values", () => {
    const publicEnv = resolvePublicEnv({
      fileValues: {
        SUPABASE_URL: "https://file.example.co",
        SUPABASE_ANON_KEY: "file-anon"
      },
      processValues: {
        SUPABASE_URL: "https://process.example.co",
        SUPABASE_ANON_KEY: "process-anon"
      }
    });

    expect(publicEnv).toEqual({
      supabaseUrl: "https://process.example.co",
      supabaseAnonKey: "process-anon"
    });
  });

  it("falls back to .env file values when process env is absent", () => {
    const publicEnv = resolvePublicEnv({
      fileValues: {
        SUPABASE_URL: "https://file.example.co",
        SUPABASE_ANON_KEY: "file-anon"
      },
      processValues: {}
    });

    expect(publicEnv).toEqual({
      supabaseUrl: "https://file.example.co",
      supabaseAnonKey: "file-anon"
    });
  });

  it("reports missing public env keys for strict builds", () => {
    const missing = getMissingPublicEnvKeys({
      supabaseUrl: "https://example.co",
      supabaseAnonKey: ""
    });

    expect(missing).toEqual(["SUPABASE_ANON_KEY"]);
  });

  it("renders runtime script with resolved env values", () => {
    const script = renderPublicEnvScript({
      supabaseUrl: "https://example.co",
      supabaseAnonKey: "anon-key"
    });

    expect(script).toContain('window.__SUPABASE_URL__ = "https://example.co";');
    expect(script).toContain('window.__SUPABASE_ANON_KEY__ = "anon-key";');
  });
});
