const authView = document.querySelector('#auth-view');
const adminPanel = document.querySelector('#admin-panel');
const authForm = document.querySelector('#auth-form');
const authMessage = document.querySelector('#auth-message');
const staffForm = document.querySelector('#staff-form');
const staffMessage = document.querySelector('#staff-message');
const staffList = document.querySelector('#admin-staff-list');
const staffCount = document.querySelector('#staff-count');
const rankSelect = document.querySelector('#staff-rank');
const departmentSelect = document.querySelector('#staff-department');
const newsForm = document.querySelector('#news-form');
const newsMessage = document.querySelector('#news-message');
const newsList = document.querySelector('#admin-news-list');
const newsCount = document.querySelector('#news-count');
const saveButton = document.querySelector('#save-staff');
const cancelButton = document.querySelector('#cancel-edit');
const saveNewsButton = document.querySelector('#save-news');
let adminToken = sessionStorage.getItem('dbr-admin-token') || '';
let editingId = null;

function setMessage(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle('is-error', isError);
}

async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (adminToken) headers.set('Authorization', `Bearer ${adminToken}`);
  if (options.body) headers.set('Content-Type', 'application/json');
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Помилка запиту (${response.status}).`);
  return data;
}

function makeOption(value, label) {
  const option = document.createElement('option');
  option.value = value;
  option.textContent = label;
  return option;
}

async function loadOptions() {
  const config = await apiRequest('/api/config');
  rankSelect.replaceChildren(makeOption('', 'Обери звання'));
  departmentSelect.replaceChildren(makeOption('', 'Обери відділ'));
  config.ranks.forEach((rank) => rankSelect.append(makeOption(rank, rank)));
  config.departments.forEach((department) => departmentSelect.append(makeOption(department, department)));
}

function makeAdminCard(employee) {
  const card = document.createElement('article');
  card.className = 'admin-staff-card';
  const image = document.createElement('img');
  image.src = employee.avatar_url;
  image.alt = '';
  image.loading = 'lazy';
  const info = document.createElement('div');
  info.className = 'admin-staff-info';
  const displayName = document.createElement('strong');
  displayName.textContent = employee.display_name;
  const details = document.createElement('span');
  details.textContent = `@${employee.username} · ${employee.rank}`;
  const department = document.createElement('small');
  department.textContent = [employee.department, employee.call_sign].filter(Boolean).join(' · ');
  info.append(displayName, details, department);
  const actions = document.createElement('div');
  actions.className = 'admin-card-actions';
  const edit = document.createElement('button');
  edit.className = 'icon-button';
  edit.type = 'button';
  edit.setAttribute('aria-label', `Редагувати ${employee.display_name}`);
  edit.innerHTML = '<i data-lucide="pencil"></i>';
  edit.addEventListener('click', () => beginEdit(employee));
  const remove = document.createElement('button');
  remove.className = 'icon-button danger-button';
  remove.type = 'button';
  remove.setAttribute('aria-label', `Видалити ${employee.display_name}`);
  remove.innerHTML = '<i data-lucide="trash-2"></i>';
  remove.addEventListener('click', () => deleteEmployee(employee));
  actions.append(edit, remove);
  card.append(image, info, actions);
  return card;
}

async function refreshStaff() {
  const employees = await apiRequest('/api/staff');
  staffList.replaceChildren();
  staffCount.textContent = String(employees.length);
  if (!employees.length) {
    const empty = document.createElement('p');
    empty.className = 'admin-empty';
    empty.textContent = 'База поки порожня. Додай першого працівника через форму.';
    staffList.append(empty);
  } else {
    employees.forEach((employee) => staffList.append(makeAdminCard(employee)));
  }
  if (window.lucide) lucide.createIcons();
}

function formatNewsDate(value) {
  const date = new Date(`${value}T12:00:00Z`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('uk-UA', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(date);
}

function makeNewsCard(news) {
  const card = document.createElement('article');
  card.className = 'admin-news-card';
  const content = document.createElement('div');
  content.className = 'admin-news-copy';
  const metadata = document.createElement('p');
  metadata.className = 'admin-news-meta';
  metadata.textContent = `${news.category} · ${formatNewsDate(news.date)}`;
  const title = document.createElement('strong');
  title.textContent = news.title;
  content.append(metadata, title);
  if (news.summary) {
    const summary = document.createElement('span');
    summary.textContent = news.summary;
    content.append(summary);
  }

  const remove = document.createElement('button');
  remove.className = 'icon-button danger-button';
  remove.type = 'button';
  remove.setAttribute('aria-label', `Видалити новину: ${news.title}`);
  remove.innerHTML = '<i data-lucide="trash-2"></i>';
  remove.addEventListener('click', () => deleteNews(news));
  card.append(content, remove);
  return card;
}

async function refreshNews() {
  const records = await apiRequest('/api/admin/news');
  newsList.replaceChildren();
  newsCount.textContent = String(records.length);
  if (!records.length) {
    const empty = document.createElement('p');
    empty.className = 'admin-empty';
    empty.textContent = 'Новин поки немає. Додай першу публікацію вище.';
    newsList.append(empty);
  } else {
    records.forEach((news) => newsList.append(makeNewsCard(news)));
  }
  if (window.lucide) lucide.createIcons();
}

async function deleteNews(news) {
  if (!window.confirm(`Видалити новину «${news.title}»?`)) return;
  try {
    await apiRequest(`/api/news/${encodeURIComponent(news.id)}`, { method: 'DELETE' });
    setMessage(newsMessage, 'Новину видалено.');
    await refreshNews();
  } catch (error) {
    setMessage(newsMessage, error.message, true);
  }
}

function showAdmin() {
  authView.classList.add('hidden');
  adminPanel.classList.remove('hidden');
  refreshStaff().catch((error) => setMessage(staffMessage, error.message, true));
  refreshNews().catch((error) => setMessage(newsMessage, error.message, true));
}

async function authenticate(candidate) {
  adminToken = candidate;
  await apiRequest('/api/admin/check');
  await loadOptions();
  sessionStorage.setItem('dbr-admin-token', adminToken);
  showAdmin();
}

function clearEditor() {
  editingId = null;
  staffForm.reset();
  document.querySelector('#staff-form-title').textContent = 'Додати працівника';
  saveButton.innerHTML = 'Додати до бази <i data-lucide="plus"></i>';
  cancelButton.classList.add('hidden');
  setMessage(staffMessage, '');
  if (window.lucide) lucide.createIcons();
}

function beginEdit(employee) {
  editingId = employee.id;
  staffForm.elements.username.value = employee.username;
  rankSelect.value = employee.rank;
  departmentSelect.value = employee.department;
  staffForm.elements.call_sign.value = employee.call_sign;
  document.querySelector('#staff-form-title').textContent = 'Редагувати працівника';
  saveButton.innerHTML = 'Зберегти зміни <i data-lucide="save"></i>';
  cancelButton.classList.remove('hidden');
  staffForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
  if (window.lucide) lucide.createIcons();
}

async function deleteEmployee(employee) {
  if (!window.confirm(`Видалити ${employee.display_name} з особового складу?`)) return;
  try {
    await apiRequest(`/api/staff/${employee.id}`, { method: 'DELETE' });
    if (editingId === employee.id) clearEditor();
    await refreshStaff();
  } catch (error) {
    setMessage(staffMessage, error.message, true);
  }
}

authForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const tokenInput = document.querySelector('#admin-token');
  setMessage(authMessage, 'Перевіряємо ключ...');
  try {
    await authenticate(tokenInput.value.trim());
  } catch (error) {
    sessionStorage.removeItem('dbr-admin-token');
    setMessage(authMessage, error.message, true);
    tokenInput.focus();
  }
});

staffForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const wasEditing = editingId !== null;
  const payload = Object.fromEntries(new FormData(staffForm));
  setMessage(staffMessage, editingId ? 'Оновлюємо запис...' : 'Шукаємо Roblox username...');
  saveButton.disabled = true;
  try {
    await apiRequest(editingId ? `/api/staff/${editingId}` : '/api/staff', {
      method: editingId ? 'PUT' : 'POST',
      body: JSON.stringify(payload)
    });
    clearEditor();
    setMessage(staffMessage, wasEditing ? 'Запис оновлено.' : 'Працівника додано до бази.');
    await refreshStaff();
  } catch (error) {
    setMessage(staffMessage, error.message, true);
  } finally {
    saveButton.disabled = false;
  }
});

function localDateInputValue() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 10);
}

newsForm.elements.date.value = localDateInputValue();
newsForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(newsForm));
  setMessage(newsMessage, 'Публікуємо новину...');
  saveNewsButton.disabled = true;
  try {
    await apiRequest('/api/news', { method: 'POST', body: JSON.stringify(payload) });
    newsForm.reset();
    newsForm.elements.date.value = localDateInputValue();
    setMessage(newsMessage, 'Новину опубліковано. Вона вже з’явилася на сайті.');
    await refreshNews();
  } catch (error) {
    setMessage(newsMessage, error.message, true);
  } finally {
    saveNewsButton.disabled = false;
  }
});

cancelButton.addEventListener('click', clearEditor);
document.querySelector('#logout-button').addEventListener('click', () => {
  sessionStorage.removeItem('dbr-admin-token');
  adminToken = '';
  adminPanel.classList.add('hidden');
  authView.classList.remove('hidden');
  authForm.reset();
  setMessage(authMessage, '');
});

(async () => {
  try {
    if (adminToken) {
      await authenticate(adminToken);
    } else {
      await loadOptions();
    }
  } catch {
    sessionStorage.removeItem('dbr-admin-token');
    adminToken = '';
    authView.classList.remove('hidden');
  }
  if (window.lucide) lucide.createIcons();
})();
