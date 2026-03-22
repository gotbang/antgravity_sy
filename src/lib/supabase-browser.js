import { createClient } from "@supabase/supabase-js";

import { getPublicEnv } from "../config/public-env.js";

let browserSupabaseClient = null;

export function getBrowserSupabase() {
  if (browserSupabaseClient) {
    return browserSupabaseClient;
  }

  const { supabaseUrl, supabaseAnonKey } = getPublicEnv();
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error("Missing public Supabase environment");
  }

  browserSupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false
    }
  });

  return browserSupabaseClient;
}
