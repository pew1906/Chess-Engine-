# ♟️ Chess Engine

A powerful and interactive Python-based Chess Engine built with **Pygame** and integrated with **Stockfish AI**. Play against an intelligent opponent with multiple difficulty levels, immersive sound effects, and customizable board themes.

---

## 🚀 Features

* ♟️ Play against AI powered by **Stockfish**
* 🎯 Multiple AI difficulty levels
* 🎨 Different chess board themes
* 🔊 Sound effects for moves and captures
* 💾 Save and load game state
* 🖱️ Interactive drag-and-drop gameplay
* ⚡ Smooth GUI built using **Pygame**
* 🧠 Intelligent move calculation

---

## 📸 Preview

![Chess Engine Preview](images/chess_preview.png)

---

## 🛠️ Tech Stack

* **Python**
* **Pygame**
* **Stockfish Chess Engine**
* JSON for game state storage

---

## 📂 Project Structure

```bash
Chess-Engine-/
│
├── images/                 # Chess pieces and board assets
├── static/
│   └── sounds/             # Sound effects
│
├── chess_gui.py            # Main game file
├── saved_game.json         # Saved game state
├── README.md
```

---

## ⚙️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/Chess-Engine-.git
cd Chess-Engine-
```

### 2️⃣ Install Dependencies

```bash
pip install pygame stockfish
```

### 3️⃣ Download Stockfish

Download Stockfish from:

👉 [https://stockfishchess.org/download/](https://stockfishchess.org/download/)

After downloading, update the Stockfish path inside `chess_gui.py`.

Example:

```python
stockfish = Stockfish(path="path/to/stockfish.exe")
```

---

## ▶️ Run the Project

```bash
python chess_gui.py
```

---

## 🎮 Controls

| Action     | Control                  |
| ---------- | ------------------------ |
| Move Piece | Drag & Drop              |
| Save Game  | Automatic / Custom Logic |
| Restart    | Re-run the program       |

---

## 🧠 AI Difficulty Levels

The engine supports multiple AI strengths using Stockfish skill levels.

Example:

```python
stockfish.set_skill_level(10)
```

| Level | Difficulty   |
| ----- | ------------ |
| 1-5   | Beginner     |
| 6-10  | Intermediate |
| 11-15 | Advanced     |
| 16-20 | Expert       |

---

## 💾 Save Game Support

Game states are stored in:

```bash
saved_game.json
```

This allows players to continue matches later.

---

## 🌟 Future Improvements

* ⏳ Chess timer support
* 🌐 Multiplayer mode
* 📜 Move history panel
* ♚ Checkmate animations
* 📊 Match statistics
* 🔥 Opening book integration

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Added new feature"
```

4. Push to GitHub

```bash
git push origin feature-name
```

5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License.

---

## 👩‍💻 Author

**Prachi Kumar**

