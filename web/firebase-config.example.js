/* TEMPLATE konfigurasi Firebase untuk dashboard.
 *
 * CARA PAKAI:
 *   1. Salin file ini menjadi `firebase-config.js` (nama persis itu).
 *   2. Isi nilainya dari Firebase Console → Project settings (⚙) → General →
 *      "Your apps" → SDK setup and configuration → Config.
 *      (Web app harus sudah didaftarkan; apiKey web aman dipublikasikan —
 *       keamanan data diatur oleh Rules, bukan oleh apiKey ini.)
 *   3. `firebase-config.js` TIDAK ikut di-commit (sudah ada di .gitignore).
 *
 * Tanpa file ini, dashboard otomatis berjalan dalam MODE DEMO (data contoh).
 */
window.FIREBASE_CONFIG = {
  apiKey: "ISI_API_KEY",
  authDomain: "NAMA-PROYEK.firebaseapp.com",
  projectId: "NAMA-PROYEK",
  storageBucket: "NAMA-PROYEK.firebasestorage.app",
  messagingSenderId: "000000000000",
  appId: "1:000000000000:web:xxxxxxxxxxxxxxxx",
};

// Nama collection Firestore — samakan dengan config.json Pi (default bed_readings).
window.FIREBASE_COLLECTION = "bed_readings";
