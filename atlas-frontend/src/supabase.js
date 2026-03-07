import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = "https://fqqczbnmjcmgnbhllgmi.supabase.co"
const SUPABASE_ANON_KEY = "sb_publishable_0WdNAq0DUblLHDu-dUev2A_YfzggNoE"

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
