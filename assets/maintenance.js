// Shared maintenance mode module for Xac Anon website.
// Import this on every page: import { checkMaintenance } from "/assets/maintenance.js";
// Then call checkMaintenance() after Firebase is initialized.

import { getDoc, doc } from "https://www.gstatic.com/firebasejs/10.4.0/firebase-firestore.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.4.0/firebase-auth.js";

const OVERLAY_HTML = `
<div id="maintenance-overlay" style="display:none;position:fixed;inset:0;z-index:9999;background:#0f0f0f;justify-content:center;align-items:center;flex-direction:column;text-align:center;padding:2rem;">
  <img src="/assets/img/xac-anon-character.png" alt="Xac Anon" class="maint-figure" />
  <h1 style="color:#ff4f81;margin:0 0 0.5rem;font-size:2.5rem;text-transform:uppercase;letter-spacing:2px;">Back Soon</h1>
  <p style="color:#aaa;margin:0 0 1.5rem;font-size:1rem;">The site is currently undergoing maintenance.</p>
  <div id="maint-message-text" style="color:#f0f0f0;background:#1a1a1a;border:1px solid #ff4f81;border-radius:10px;padding:1rem 2rem;box-shadow:0 0 15px #ff4f81;max-width:480px;line-height:1.7;font-size:1.1rem;">We'll be back soon. Thanks for your patience!</div>
  <div style="margin-top:2rem;display:flex;gap:1.2rem;justify-content:center;">
    <a href="https://instagram.com/xacanon/" target="_blank" rel="noopener" style="color:#f0f0f0;font-size:1.6rem;"><i class="fab fa-instagram"></i></a>
    <a href="https://x.com/xacanonau" target="_blank" rel="noopener" style="color:#f0f0f0;font-size:1.6rem;"><i class="fab fa-x-twitter"></i></a>
    <a href="https://youtube.com/@XacAnonRS" target="_blank" rel="noopener" style="color:#f0f0f0;font-size:1.6rem;"><i class="fab fa-youtube"></i></a>
  </div>
</div>
`;

const OVERLAY_CSS = `
@keyframes maintFloat { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-15px) rotate(1deg); } }
.maint-figure { width: min(220px, 60vw); height: auto; margin-bottom: 1.5rem; filter: drop-shadow(0 0 15px rgba(255, 79, 129, 0.4)); animation: maintFloat 4s infinite ease-in-out; }
`;

// Inject CSS once
const styleEl = document.createElement("style");
styleEl.textContent = OVERLAY_CSS;
document.head.appendChild(styleEl);

/**
 * Check Firestore for maintenance mode and show overlay if enabled.
 * Logged-in users bypass the overlay.
 * @param {import('firebase/firestore').Firestore} db
 * @param {import('firebase/auth').Auth} auth
 */
export async function checkMaintenance(db, auth) {
  // Inject overlay HTML if not already present
  if (!document.getElementById("maintenance-overlay")) {
    const div = document.createElement("div");
    div.innerHTML = OVERLAY_HTML.trim();
    document.body.prepend(div.firstElementChild);
  }

  const overlay = document.getElementById("maintenance-overlay");
  const msgEl = document.getElementById("maint-message-text");

  try {
    const snap = await getDoc(doc(db, "siteSettings", "maintenance"));
    if (snap.exists() && snap.data().enabled === true) {
      if (snap.data().message && msgEl) {
        msgEl.textContent = snap.data().message;
      }
      overlay.style.display = "flex";
      document.body.style.overflow = "hidden";

      onAuthStateChanged(auth, (user) => {
        if (user) {
          overlay.style.display = "none";
          document.body.style.overflow = "auto";
        }
      });
    }
  } catch (err) {
    console.warn("Maintenance check failed:", err);
  }
}
