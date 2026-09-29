const ticker = document.querySelector('#header-news-ticker');

async function loadLatestNews() {
  if (!ticker) return;
  try {
    const response = await fetch('data/news.json');
    if (!response.ok) return;
    const news = await response.json();
    if (!Array.isArray(news) || news.length === 0) return;

    const latest = [...news]
      .filter((item) => item && item.title && item.date)
      .sort((left, right) => right.date.localeCompare(left.date))[0];
    if (!latest) return;

    ticker.querySelector('#header-news-title').textContent = latest.title;
    ticker.querySelector('#header-news-date').textContent = new Intl.DateTimeFormat('uk-UA', {
      day: 'numeric',
      month: 'long',
      timeZone: 'UTC'
    }).format(new Date(`${latest.date}T12:00:00Z`));
    ticker.setAttribute('aria-label', `Остання новина: ${latest.title}. Відкрити всі новини.`);
  } catch {
    // Keep the static fallback label if news data is temporarily unavailable.
  }
}

loadLatestNews();
