const newsList = document.querySelector('#news-list');
const newsStatus = document.querySelector('#news-status');
const newsSearch = document.querySelector('#news-search');
const categorySelect = document.querySelector('#news-category');
const newsTotal = document.querySelector('#news-total');
let allNews = [];

function textElement(tagName, className, value) {
  const element = document.createElement(tagName);
  element.className = className;
  element.textContent = value;
  return element;
}

function formatDate(value) {
  const date = new Date(`${value}T12:00:00Z`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('uk-UA', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC'
  }).format(date);
}

function createNewsCard(item, index) {
  const article = document.createElement('article');
  article.className = 'news-card';
  article.append(textElement('span', 'news-card-index', String(index + 1).padStart(2, '0')));

  const metadata = document.createElement('div');
  metadata.className = 'news-card-meta';
  const category = textElement('span', 'news-category-tag', item.category || 'Новина');
  const date = document.createElement('time');
  date.dateTime = item.date;
  date.textContent = formatDate(item.date);
  metadata.append(category, date);

  const copy = document.createElement('div');
  copy.className = 'news-card-copy';
  copy.append(metadata, textElement('h3', 'news-card-title', item.title));
  if (item.summary) copy.append(textElement('p', 'news-card-summary', item.summary));

  const body = document.createElement('div');
  body.className = 'news-card-body';
  const paragraphs = Array.isArray(item.content) ? item.content : [item.content || ''];
  paragraphs.filter(Boolean).forEach((paragraph) => body.append(textElement('p', '', paragraph)));

  article.append(copy, body);
  return article;
}

function renderNews() {
  const searchTerm = newsSearch.value.trim().toLocaleLowerCase('uk-UA');
  const selectedCategory = categorySelect.value;
  const visibleNews = allNews.filter((item) => {
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    const searchableText = `${item.title} ${item.summary || ''} ${(item.content || []).toString()}`.toLocaleLowerCase('uk-UA');
    return matchesCategory && searchableText.includes(searchTerm);
  });

  newsList.replaceChildren();
  if (!visibleNews.length) {
    const emptyText = allNews.length
      ? 'За цим запитом новин не знайдено.'
      : 'Поки що новин немає. Нові повідомлення з’являться тут.';
    newsList.append(textElement('p', 'news-empty', emptyText));
    newsStatus.textContent = allNews.length ? '' : 'БЮЛЕТЕНЬ ОЧІКУЄ ПЕРШОЇ ПУБЛІКАЦІЇ';
    return;
  }

  newsStatus.textContent = `${visibleNews.length} ${visibleNews.length === 1 ? 'ПУБЛІКАЦІЯ' : 'ПУБЛІКАЦІЙ'}`;
  visibleNews.forEach((item, index) => newsList.append(createNewsCard(item, index)));
}

async function loadNews() {
  try {
    const response = await fetch('data/news.json');
    if (!response.ok) throw new Error('Не вдалося завантажити стрічку новин.');
    const payload = await response.json();
    if (!Array.isArray(payload)) throw new Error('Файл новин має містити JSON-масив.');
    allNews = payload
      .filter((item) => item && item.title && item.date)
      .sort((left, right) => right.date.localeCompare(left.date));

    const categories = [...new Set(allNews.map((item) => item.category).filter(Boolean))]
      .sort((left, right) => left.localeCompare(right, 'uk'));
    categories.forEach((categoryName) => categorySelect.append(textElement('option', '', categoryName)));
    newsTotal.textContent = `${String(allNews.length).padStart(2, '0')} ${allNews.length === 1 ? 'ПУБЛІКАЦІЯ' : 'ПУБЛІКАЦІЙ'}`;
    newsStatus.textContent = '';
    renderNews();
  } catch (error) {
    newsStatus.textContent = error.message;
    newsStatus.classList.add('staff-status-error');
  }
}

newsSearch.addEventListener('input', renderNews);
categorySelect.addEventListener('change', renderNews);
loadNews();
