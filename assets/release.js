// Works out what the home countdown and the music page presave button show.
// Data comes from /data/latest-release.json (refreshed by a GitHub Action from
// Apple Music). A countdown set in the admin panel overrides it while its date
// is still in the future.
window.XacRelease = (() => {
  let data;
  const load = () =>
    (data ??= fetch('/data/latest-release.json', { cache: 'no-cache' })
      .then(r => (r.ok ? r.json() : {}))
      .catch(() => ({})));

  const withDate = r => r && { ...r, date: new Date(r.releaseDate) };

  // override: { label, releaseDate: Date, presaveUrl } from Firestore, or null
  async function resolve(override) {
    const { upcoming, latest } = await load();
    const now = Date.now();
    const up = withDate(upcoming);

    if (override && override.releaseDate instanceof Date && override.releaseDate.getTime() > now) {
      return {
        mode: 'upcoming',
        heading: override.label || 'Next Release',
        title: up && Math.abs(up.date - override.releaseDate) < 864e5 ? up.title : '',
        date: override.releaseDate,
        link: override.presaveUrl || (up && up.link) || '',
      };
    }
    if (up && up.date.getTime() > now) {
      return { mode: 'upcoming', heading: 'Next Release', ...up };
    }
    // An "upcoming" release that has since come out is the newest one.
    const newest = up || withDate(latest);
    return newest ? { mode: 'latest', heading: 'Latest Release', ...newest } : null;
  }

  return { resolve };
})();
