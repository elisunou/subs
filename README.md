<img width="157" height="157" alt="logo" src="https://github.com/user-attachments/assets/d94103ee-0664-485d-b462-fc5330f1ca7f" />


# Subs.ro – Extensie Avansată pentru Subtitrări Kodi

> **Extensie inteligentă pentru subtitrări în limba română pentru Kodi, cu potrivire automată avansată**

---

## 📋 Prezentare generală

**Subs.ro** este o extensie avansată de subtitrări pentru Kodi care oferă detectare și descărcare automată a subtitrărilor în limba română de pe Subs.ro, folosind un algoritm sofisticat de potrivire inteligentă.

Extensia se integrează perfect în centrul media Kodi și oferă potriviri precise pe baza informațiilor despre versiune, calitatea sursei și metadatele episodului — fără a necesita configurare manuală complexă.

---

## ✨ Caracteristici principale

### 🎯 Algoritm de potrivire inteligentă

* **Sistem de notare avansat** pentru calcularea celei mai bune potriviri
* Potrivire multi-factor:

  * detectare episod/sezon
  * grup de lansare
  * sursă (BluRay / WEB-DL / HDTV etc.)
* Detectare automată a limbii și a diacriticelor românești (ă, â, î, ș, ț)
* Gestionarea fișierelor arhivă cu episoade multiple

---

### 🚀 Optimizare performanță

* **Sistem de cache local (SQLite)** pentru reducerea apelurilor API
* Stocarea rezultatelor căutării pentru acces rapid
* Monitorizarea cotei API pentru prevenirea limitării ratei
* Gestionare eficientă a memoriei pentru baze mari de subtitrări

---

### 📦 Suport avansat pentru arhive

* **Suport VFS (Virtual File System)** pentru arhive ZIP și RAR
* Nu este necesară extragerea — redare directă din arhivă
* Detectare automată a fișierului corect din arhivă
* Suport pentru arhive cu mai multe episoade

---

### 🎬 Potrivire informații media

* Detectare automată sezon/episod din numele fișierului video
* Identificare grup de lansare
* Detectare sursă (BluRay, WEB-DL, HDTV, DVDRip etc.)
* Detectare traducător/furnizor (Netflix, HBO, Amazon etc.)

---

### ⚙️ Setări personalizabile

* **Moduri de descărcare:**

  * Auto (automat)
  * Manual (selecție utilizator)
  * Întreabă (confirmare înainte de descărcare)
* Prag minim de scor pentru descărcare automată
* Detectare automată a codificării
* Sistem configurabil de notificări
* Opțiuni extinse de depanare

---

### 🌍 Suport multi-limbă

* Interfață complet tradusă în română
* Interfață în limba engleză
* Ușor de extins pentru limbi suplimentare

---

### 📊 Gestionare API

* Monitorizare cotă cu avertismente în timp real
* Validare cheie API la pornire
* Gestionare erori cu mesaje prietenoase
* Mecanisme automate de reîncercare

---

## 📥 Instalare

### Cerințe preliminare

* **Kodi** versiunea 21.0 sau mai nouă (Python 3.x)
* Cont activ pe Subs.ro
* Cheie API gratuită

---

### Pași de instalare

#### 1️⃣ Obținerea cheii API

* Accesați: [https://subs.ro/api](https://subs.ro/api)
* Autentificați-vă în cont
* Generați sau copiați cheia API

---

#### 2️⃣ Instalarea extensiei

1. Descărcați extensia (fișier ZIP).
2. În Kodi accesați:
   `Setări → Extensii → Instalare din fișier ZIP`
3. Selectați fișierul descărcat.
4. Instalați dependențele când vi se solicită.

---

#### 3️⃣ Configurare

Accesați:
`Extensii → Extensiile mele → Subtitrări → Subs.ro → Setări`

* Introduceți cheia API
* Ajustați preferințele dorite

---

#### 4️⃣ Utilizare

1. Redați un videoclip.
2. Apăsați `C` (sau butonul dedicat subtitrărilor).
3. Selectați **Subs.ro** din lista surselor.
4. Subtitrarea optimă va fi selectată automat.

---

## ⚙️ Configurare

| Setare               | Implicit    | Descriere                             |
| -------------------- | ----------- | ------------------------------------- |
| Cheie API            | Obligatoriu | Cheia API subs.ro                     |
| Mod descărcare       | Auto        | Auto / Manual / Întreabă              |
| Durată cache         | 7 zile      | Perioada de stocare a rezultatelor    |
| Activare notificări  | Activat     | Afișează mesaje de succes/eroare      |
| Jurnal depanare      | Dezactivat  | Activează log detaliat                |
| Scor minim potrivire | 70%         | Prag minim pentru descărcare automată |

---

## 🔧 Detalii tehnice

### Arhitectură

* Limbaj: Python 3.x
* API: REST Subs.ro v1.0
* Stocare: SQLite (cache local)
* Formate suportate: SRT, ASS, SUB, MicroDVD, VobSub etc.
* Arhive suportate: ZIP, RAR (prin VFS)

---

### Dependențe

* `xbmc.python >= 3.0.0`
* `script.module.requests >= 2.31.0`

---

### Funcții principale

* `get_api_key()` – Validare acreditări
* `search_subtitles()` – Interogare API și potrivire
* `score_matches()` – Calcul scor inteligent
* `download_subtitle()` – Descărcare și gestionare VFS
* `validate_encoding()` – Detectare și corectare codificare

---

## 📊 Algoritm de potrivire

```
Scor final =
  (Potrivire episod × 40%) +
  (Potrivire grup lansare × 30%) +
  (Potrivire calitate sursă × 20%) +
  (Potrivire limbă/codificare × 10%)
```

### Factori de notare

* Detectare sezon/episod
* Potrivire grup de lansare
* Prioritizare calitate: BluRay > WEB-DL > HDTV
* Ajustare pentru codificare și diacritice

---

## 🐛 Depanare

### Cheie API invalidă

* Verificați dacă nu există spații suplimentare
* Confirmați că contul este activ
* Regenerați cheia API

---

### Nu se găsesc subtitrări

* Asigurați-vă că numele fișierului conține informații despre sezon/episod
* Verificați cota API
* Activați jurnalul de depanare

Log Kodi:

```
~/.kodi/temp/kodi.log
```

Căutați intrări cu `[Subs.ro]`.

---

### Probleme cu diacriticele

Extensia detectează automat codificarea.
Dacă apar probleme, setați manual codificarea în setări.

---

## 📝 Istoric versiuni

### v2.0.0 (26.01.2026)

* Algoritm inteligent de potrivire
* Sistem cache local
* Monitorizare cotă API
* Suport VFS pentru ZIP/RAR
* Detectare automată codificare
* Gestionare arhive multi-episod
* Moduri descărcare configurabile
* Detectare prioritate traducător
* Sistem notificări personalizabil
* Opțiuni extinse de depanare
* Traducere completă în română

---

### v1.0.0

* Funcționalitate de bază căutare și descărcare
* Integrare API subs.ro

---

## 🤝 Contribuții

Contribuțiile sunt binevenite:

1. Faceți fork la depozit
2. Creați o ramură:

   ```
   git checkout -b feature/noua-functionalitate
   ```
3. Faceți commit:

   ```
   git commit -m "Adaugă funcționalitate nouă"
   ```
4. Trimiteți modificările:

   ```
   git push origin feature/noua-functionalitate
   ```
5. Deschideți un Pull Request

---

## 📄 Licență

Acest proiect este licențiat sub **GPL-3.0**.
Consultați fișierul LICENSE pentru detalii.

---

## 🔗 Resurse

* Site oficial: [https://subs.ro](https://subs.ro)
* Documentație API: [https://subs.ro/api](https://subs.ro/api)
* Forum Kodi: [https://forum.kodi.tv](https://forum.kodi.tv)
* Wiki Kodi: [https://kodi.wiki](https://kodi.wiki)

---

## 👤 Autor

**elisunou** – Creator și întreținător

---

## ⭐ Suport

Dacă extensia vă este utilă:

* ⭐ Acordați o stea pe GitHub
* 🐛 Raportați probleme
* 💬 Participați la discuții pe forum
* 📝 Lăsați o recenzie pe Subs.ro

---

## ⚠️ Disclaimer

* Necesită cheie API gratuită de la Subs.ro
* Subtitrările sunt furnizate de comunitatea Subs.ro
* Respectați legislația privind drepturile de autor
* Extensia nu este afiliată oficial cu Subs.ro

---

## 🚀 Pornire rapidă

1. Instalați extensia din ZIP
2. Introduceți cheia API
3. Redați un videoclip
4. Apăsați `C`
5. Selectați „Subs.ro”
6. Bucurați-vă de subtitrări în limba română 🎬

---

**Realizat cu ❤️ pentru comunitatea utilizatorilor Kodi din România**
