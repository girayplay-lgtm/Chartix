import {
  auth,
  googleProvider
} from "./firebase-config.js";

import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

window.CHARTIX_USER = null;

const Auth = {
  init() {
    const modal = document.getElementById("authModal");
    const loginBtn = document.getElementById("loginBtn");
    const closeAuth = document.getElementById("closeAuth");
    const googleLogin = document.getElementById("googleLogin");
    const emailLogin = document.getElementById("emailLogin");

    loginBtn.textContent = "Login";

    loginBtn.addEventListener("click", async () => {
      if (window.CHARTIX_USER) {
        const ok = confirm("Sign out from CHARTIX?");
        if (ok) await signOut(auth);
        return;
      }

      modal.style.display = "grid";
    });

    closeAuth.addEventListener("click", () => {
      modal.style.display = "none";
    });

    googleLogin.addEventListener("click", async () => {
      try {
        await signInWithPopup(auth, googleProvider);
        modal.style.display = "none";
      } catch (err) {
        alert("Google login failed. Check Firebase config.");
        console.error(err);
      }
    });

    emailLogin.addEventListener("click", async () => {
      const email = document.getElementById("emailInput").value.trim().toLowerCase();
      const password = document.getElementById("passwordInput").value.trim();

      if (!email || !password) {
        alert("Enter email and password.");
        return;
      }

      try {
        await signInWithEmailAndPassword(auth, email, password);
        modal.style.display = "none";
      } catch {
        try {
          await createUserWithEmailAndPassword(auth, email, password);
          modal.style.display = "none";
        } catch (err2) {
          alert("Email login/register failed. Check Firebase settings.");
          console.error(err2);
        }
      }
    });

    onAuthStateChanged(auth, user => {
      window.CHARTIX_USER = user || null;
      loginBtn.textContent = user ? "Account" : "Login";

      if (window.refreshUserWatchlist) {
        window.refreshUserWatchlist();
      }
    });
  }
};

Auth.init();
