import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";

import {
    getAuth,
    GoogleAuthProvider
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

import {
    getFirestore
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js";

const firebaseConfig = {
    apiKey: "AIzaSyBn7Im0qLfWWD57pi9-cv1mHTm7DrP_iEA",
    authDomain: "chartix-7183f.firebaseapp.com",
    projectId: "chartix-7183f",
    storageBucket: "chartix-7183f.firebasestorage.app",
    messagingSenderId: "47315740168",
    appId: "1:47315740168:web:8eed2d6ceadb5387fed3bd",
    measurementId: "G-PYYRHFY45T"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();