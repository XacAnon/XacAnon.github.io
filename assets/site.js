// Shared setup for the newer pages (shows, videos, links, release pages):
// Firebase connection, the menu from the admin panel, and the mobile menu button.
import { initializeApp, getApps } from "https://www.gstatic.com/firebasejs/10.4.0/firebase-app.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/10.4.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyD5ErOWtxBdfL3Z0o_TwYnii1GflZ0fYdc",
  authDomain: "xacanonwebsite.firebaseapp.com",
  projectId: "xacanonwebsite",
  storageBucket: "xacanonwebsite.firebasestorage.app",
  messagingSenderId: "725682557903",
  appId: "1:725682557903:web:f699e7cb0504a8d75478ba",
};

export const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
export const db = getFirestore(app);

function bindMenu(root) {
  const hb = root.querySelector(".hamburger");
  const nl = root.querySelector(".nav-links");
  if (hb && nl && !hb._bound) {
    hb._bound = true;
    hb.addEventListener("click", () => nl.classList.toggle("active"));
  }
}

const nav = document.querySelector(".navbar-container");
if (nav) {
  bindMenu(nav);
  getDoc(doc(db, "siteSettings", "globalMenu")).then(snap => {
    if (!snap.exists() || !snap.data().htmlCode) return;
    const logo = nav.querySelector(".nav-logo");
    nav.innerHTML = snap.data().htmlCode;
    if (logo && !nav.querySelector(".nav-logo")) nav.prepend(logo);
    bindMenu(nav);
  }).catch(err => console.warn("Menu:", err));
}

export const escapeHtml = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
