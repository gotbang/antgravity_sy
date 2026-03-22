function readMetaContent(name) {
  if (typeof document === "undefined") {
    return "";
  }

  return document.querySelector(`meta[name="${name}"]`)?.getAttribute("content") ?? "";
}

const publicEnv = Object.freeze({
  supabaseUrl: globalThis.__SUPABASE_URL__ ?? readMetaContent("supabase-url"),
  supabaseAnonKey: globalThis.__SUPABASE_ANON_KEY__ ?? readMetaContent("supabase-anon-key")
});

export function getPublicEnv() {
  return publicEnv;
}

export function hasPublicSupabaseEnv() {
  return Boolean(publicEnv.supabaseUrl && publicEnv.supabaseAnonKey);
}
