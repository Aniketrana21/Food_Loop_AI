import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://cskzbogqwiqzwciuviow.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'sb_publishable_KOX8cTLR2U2fv4k3VsTxhA_EvH1QNcN';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
