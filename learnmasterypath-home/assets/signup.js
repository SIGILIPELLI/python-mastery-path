/* Mastery Path email sign-up box (shared by the hub and every course site).
 * Renders into #mp-signup if present; otherwise appends to the end of a course lesson.
 * Posts to the Cloudflare Worker at api.learnmasterypath.com/api/subscribe. */
(function () {
  var API = 'https://api.learnmasterypath.com/api/subscribe';
  var PACK = 'https://learnmasterypath.com/interview-pack/';
  var PRIVACY = 'https://learnmasterypath.com/privacy.html';

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  function track(name, params) { try { if (window.gtag) window.gtag('event', name, params || {}); } catch (e) {} }

  function courseSlug() {
    var seg = location.pathname.split('/').filter(Boolean);
    for (var i = seg.length - 1; i >= 0; i--) if (/-mastery-path$/.test(seg[i])) return seg[i];
    return location.pathname === '/' ? 'home' : (seg[0] || 'home');
  }

  var CSS = '' +
    '.mp-su{margin:2.2em 0 1em;padding:20px 22px;border:1px solid rgba(47,169,141,.35);border-radius:14px;' +
    'background:linear-gradient(135deg,rgba(47,169,141,.10),rgba(47,169,141,.03));font-size:15px;line-height:1.5}' +
    '.mp-su h3{margin:0 0 6px!important;font-size:1.15em!important;font-weight:700}' +
    '.mp-su p{margin:0 0 12px!important}' +
    '.mp-su form{display:flex;flex-wrap:wrap;gap:8px}' +
    '.mp-su input[type=email]{flex:1 1 220px;min-width:0;padding:10px 12px;border-radius:9px;border:1px solid rgba(127,127,127,.45);' +
    'font:inherit;background:var(--md-default-bg-color,#fff);color:inherit}' +
    '.mp-su button{padding:10px 16px;border:0;border-radius:9px;background:#2FA98D;color:#fff;font:inherit;font-weight:600;cursor:pointer}' +
    '.mp-su button[disabled]{opacity:.6;cursor:wait}' +
    '.mp-su .mp-su-hp{position:absolute!important;left:-9999px!important;width:1px;height:1px;overflow:hidden}' +
    '.mp-su small{display:block;margin-top:8px;opacity:.75;font-size:.82em}' +
    '.mp-su .mp-su-msg{margin-top:10px;font-weight:600}' +
    '.mp-su .mp-su-err{color:#c0392b}' +
    '.mp-su a.mp-su-cta{display:inline-block;margin-top:4px;padding:9px 14px;border-radius:9px;background:#2FA98D;color:#fff!important;text-decoration:none;font-weight:600}';

  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (html) e.innerHTML = html;
    return e;
  }

  function doneView(box, returning) {
    box.innerHTML = '<h3>' + (returning ? 'Welcome back!' : 'You’re in! 🎉') + '</h3>' +
      '<p>Your free Interview Prep Pack is ready. We’ll also email you when new courses go live.</p>' +
      '<a class="mp-su-cta" href="' + PACK + '">Open the Interview Prep Pack →</a>';
  }

  function render(box) {
    box.className = 'mp-su';
    if (store('mp_sub') === '1') {
      box.innerHTML = '<p style="margin:0!important">📘 <strong>Your Interview Prep Pack:</strong> ' +
        '<a href="' + PACK + '">open the 72 questions &amp; answers →</a></p>';
      return;
    }
    box.innerHTML =
      '<h3>🎁 Free Interview Prep Pack</h3>' +
      '<p>72 real interview questions with model answers — Python, Java, JavaScript, SQL, Excel, Tally &amp; GST, ' +
      'digital marketing, AWS and the HR round. Enter your email to unlock it, and get notified when new free courses go live.</p>' +
      '<form novalidate>' +
      '<input type="email" name="email" placeholder="you@example.com" autocomplete="email" required aria-label="Email address">' +
      '<span class="mp-su-hp" aria-hidden="true"><input type="text" name="website" tabindex="-1" autocomplete="off"></span>' +
      '<button type="submit">Send me the pack</button>' +
      '</form>' +
      '<small>Free. No spam — unsubscribe anytime. See our <a href="' + PRIVACY + '">privacy policy</a>.</small>' +
      '<div class="mp-su-msg" role="status" aria-live="polite"></div>';
    var form = box.querySelector('form');
    var msg = box.querySelector('.mp-su-msg');
    var btn = form.querySelector('button');
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var email = form.email.value.trim();
      msg.className = 'mp-su-msg';
      if (!/^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(email)) { msg.className += ' mp-su-err'; msg.textContent = 'Please enter a valid email address.'; return; }
      btn.disabled = true; btn.textContent = 'Sending…'; msg.textContent = '';
      fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, interest: courseSlug(), page: location.pathname, website: form.website.value })
      }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (!res.ok) throw new Error(res.d && res.d.error || 'Something went wrong.');
          store('mp_sub', '1');
          track('generate_lead', { method: 'interview_pack', course: courseSlug() });
          doneView(box, res.d.returning);
        })
        .catch(function (err) {
          btn.disabled = false; btn.textContent = 'Send me the pack';
          msg.className += ' mp-su-err';
          msg.textContent = err.message || 'Network error. Please try again.';
        });
    });
  }

  function mount() {
    if (document.querySelector('.mp-su')) return;
    var target = document.getElementById('mp-signup');
    if (!target) {
      var article = document.querySelector('article.md-content__inner');
      if (!article) return;
      target = el('div', { id: 'mp-signup' });
      article.appendChild(target);
    }
    document.head.appendChild(el('style', {}, CSS));
    render(target);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
