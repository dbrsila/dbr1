// Anon-ключ публічний — це нормально. НІКОЛИ не вставляй сюди service_role ключ.
const SUPABASE_URL = 'https://cstsgheopotszylkkigb.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_epuZNPEZUC3FEXODkfqE1g_JHEWr0bq';

window.db = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Списки для форми адмінки (раніше приходили з /api/config) — впиши свої
window.DBR_RANKS = ['Курсант', 'Капрал', 'Сержант', 'Старший Сержант', 'Молодший Лейтенант', 'Лейтенант', 'Старший Лейтенант', 'Капітан', 'Майор', 'Підполковник', 'Полковник', 'Заступник Директора ДБР', 'Директор ДБР'];
window.DBR_DEPARTMENTS = ['ТСВ', 'ОСД','Керівництво ДБР'];

// Службова пошта адміна (на сайті не показується, вводити її не треба)
window.DBR_ADMIN_EMAIL = 'admin@dbr-site.com';
