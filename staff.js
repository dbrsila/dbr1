const staffGrid = document.querySelector('#staff-grid');
const staffStatus = document.querySelector('#staff-status');

function makeTextElement(tag, className, text) {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}

function createStaffCard(employee) {
  const card = document.createElement('article');
  card.className = 'staff-card glass reveal';

  const portrait = document.createElement('img');
  portrait.className = 'staff-portrait';
  portrait.src = employee.avatar_url;
  portrait.alt = `Аватар Roblox: ${employee.display_name}`;
  portrait.loading = 'lazy';
  portrait.referrerPolicy = 'no-referrer';
  portrait.addEventListener('error', () => {
    portrait.replaceWith(makeTextElement('span', 'staff-avatar-fallback', employee.display_name.slice(0, 2).toUpperCase()));
  }, { once: true });

  const top = document.createElement('div');
  top.className = 'staff-card-top';
  const identity = document.createElement('div');
  identity.className = 'staff-identity';
  identity.append(portrait, makeTextElement('span', 'staff-call-sign', employee.call_sign || employee.department));
  top.append(identity, makeTextElement('span', 'staff-active', 'НА СЛУЖБІ'));

  const name = makeTextElement('h3', 'staff-name', employee.display_name);
  const username = makeTextElement('p', 'staff-username', `@${employee.username}`);
  const rank = makeTextElement('p', 'staff-rank', employee.rank);
  const footer = document.createElement('div');
  footer.className = 'staff-card-footer';
  const viewLink = document.createElement('a');
  viewLink.className = 'staff-view-button';
  viewLink.href = employee.profile_url;
  viewLink.target = '_blank';
  viewLink.rel = 'noopener noreferrer';
  viewLink.setAttribute('aria-label', `Відкрити 3D-профіль Roblox: ${employee.display_name}`);
  viewLink.innerHTML = '<i data-lucide="scan-face" class="h-4 w-4"></i><span>3D-аватар Roblox</span><i data-lucide="arrow-up-right" class="h-3.5 w-3.5"></i>';
  footer.append(rank, viewLink);
  card.append(top, name, username, footer);
  return card;
}

async function loadStaff() {
  staffStatus.textContent = 'Завантажуємо особовий склад...';
  let staff;
  try {
    const configResponse = await fetch('pages-config.json');
    const config = configResponse.ok ? await configResponse.json() : { static: false };
    if (config.static) {
      const response = await fetch('data/staff.json');
      if (!response.ok) throw new Error('Не вдалося завантажити особовий склад.');
      staff = await response.json();
    } else {
      const response = await fetch('api/staff');
      if (!response.ok) throw new Error('Не вдалося отримати список працівників.');
      staff = await response.json();
    }
    staffGrid.replaceChildren();
    if (!staff.length) {
      staffStatus.textContent = 'Особовий склад ще не додано.';
      return;
    }
    staffStatus.textContent = `${staff.length} ${staff.length === 1 ? 'працівник' : 'працівників'} у складі ДБР`;
    staff.forEach((employee) => staffGrid.append(createStaffCard(employee)));
    if (window.lucide) lucide.createIcons();
    requestAnimationFrame(() => staffGrid.querySelectorAll('.reveal').forEach((card) => card.classList.add('is-visible')));
  } catch (error) {
    staffStatus.textContent = error.message;
    staffStatus.classList.add('staff-status-error');
  }
}

loadStaff();
