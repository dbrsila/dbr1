// Anon-ключ публічний — це нормально. НІКОЛИ не вставляй сюди service_role ключ.
const SUPABASE_URL = 'https://cstsgheopotszylkkigb.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_epuZNPEZUC3FEXODkfqE1g_JHEWr0bq';

window.db = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Списки для форми адмінки (раніше приходили з /api/config) — впиши свої
window.DBR_RANKS = ['Курсант', 'Капрал', 'Сержант', 'Старший Сержант', 'Молодший Лейтенант', 'Лейтенант', 'Старший Лейтенант', 'Капітан', 'Майор', 'Підполковник', 'Полковник'];
window.DBR_DEPARTMENTS = ['Відділ 1', 'Відділ 2'];

// Службова пошта адміна (на сайті не показується, вводити її не треба)
window.DBR_ADMIN_EMAIL = 'admin@dbr-site.com';
