import sys
import random
import time
import csv
import pyttsx3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QMessageBox, QHBoxLayout, QTextEdit, QLineEdit
)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


class BloodSugarMonitor(QWidget):
    def __init__(self):
        super().__init__()

        self.blood_sugar_values = []
        self.time_stamps = []

        self.low_history = []
        self.high_history = []
        self.critical_history = []

        self.engine = pyttsx3.init()

        self.initUI()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5000)

    def initUI(self):
        self.setWindowTitle("🩸 Blood Sugar Monitor")
        self.setGeometry(100, 100, 850, 850)
        self.setStyleSheet("background-color: #f5f6fa; font-family: 'Segoe UI';")

        layout = QVBoxLayout()

        # Top banner
        self.banner_label = QLabel()
        pixmap = QPixmap("logo.png")
        self.banner_label.setPixmap(pixmap)
        self.banner_label.setFixedHeight(100)
        self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setScaledContents(True)
        layout.addWidget(self.banner_label)

        self.label_title = QLabel("🩸 Real-Time Blood Sugar Monitor")
        self.label_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        self.label_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_title)

        self.label_value = QLabel("-- mg/dL")
        self.label_value.setStyleSheet("font-size: 30px; font-weight: bold; color: black;")
        self.label_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_value)

        self.label_condition = QLabel("Waiting for reading...")
        self.label_condition.setStyleSheet("font-size: 18px;")
        self.label_condition.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_condition)

        self.label_time = QLabel("Time: --:--:--")
        self.label_time.setStyleSheet("font-size: 14px;")
        self.label_time.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_time)

        self.label_suggestion = QLabel("")
        self.label_suggestion.setStyleSheet("font-size: 14px; color: #2980b9;")
        self.label_suggestion.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_suggestion)

        # History
        self.history_button = QPushButton("🧾 View History")
        self.history_button.clicked.connect(self.toggle_history_visibility)
        self.set_button_style(self.history_button)
        layout.addWidget(self.history_button)

        self.history_layout = QVBoxLayout()
        self.recent_low = QLabel("🟥 Low:\n--")
        self.recent_low.setStyleSheet("font-size: 14px; color: red; white-space: pre-line;")
        self.history_layout.addWidget(self.recent_low)

        self.recent_high = QLabel("🟧 High:\n--")
        self.recent_high.setStyleSheet("font-size: 14px; color: orange; white-space: pre-line;")
        self.history_layout.addWidget(self.recent_high)

        self.recent_critical = QLabel("🔴 Critical:\n--")
        self.recent_critical.setStyleSheet("font-size: 14px; color: darkred; white-space: pre-line;")
        self.history_layout.addWidget(self.recent_critical)

        self.history_container = QWidget()
        self.history_container.setLayout(self.history_layout)
        self.history_container.hide()
        layout.addWidget(self.history_container)

        # Graph
        self.figure, self.ax = plt.subplots(figsize=(7, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("💾 Save Data to CSV")
        self.save_button.clicked.connect(self.save_to_csv)
        self.set_button_style(self.save_button)
        button_layout.addWidget(self.save_button)

        self.chatbot_button = QPushButton("💬 Open Chatbot")
        self.chatbot_button.clicked.connect(self.toggle_chatbot)
        self.set_button_style(self.chatbot_button)
        button_layout.addWidget(self.chatbot_button)

        layout.addLayout(button_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #2980b9; font-size: 14px;")
        layout.addWidget(self.status_label)

        # Chatbot
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: #f4f4f4; font-size: 14px; padding: 10px;")
        self.chat_display.hide()
        layout.addWidget(self.chat_display)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask a health-related question...")
        self.chat_input.returnPressed.connect(self.handle_chat)
        self.chat_input.hide()
        layout.addWidget(self.chat_input)

        self.setLayout(layout)

    def set_button_style(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

    def toggle_history_visibility(self):
        if self.history_container.isVisible():
            self.history_container.hide()
            self.history_button.setText("🧾 View History")
        else:
            self.history_container.show()
            self.history_button.setText("❌ Hide History")

    def get_blood_sugar(self):
        return round(random.uniform(60, 200), 2)

    def check_condition(self, value):
        if value < 70:
            return "Low Blood Sugar (Hypoglycemia)", "red", "Eat a fast-acting sugar (juice, candy, glucose tablets)."
        elif 70 <= value < 140:
            return "Normal Blood Sugar", "green", ""
        elif 140 <= value < 180:
            return "High Blood Sugar (Pre-Diabetes)", "orange", "Drink water, go for a walk, and reduce sugar intake."
        else:
            return "Critical High Blood Sugar! (Diabetes Alert)", "darkred", "Consult a doctor, take insulin if prescribed."

    def update_data(self):
        value = self.get_blood_sugar()
        timestamp = time.strftime("%H:%M:%S")

        self.blood_sugar_values.append(value)
        self.time_stamps.append(timestamp)

        if len(self.blood_sugar_values) > 20:
            self.blood_sugar_values.pop(0)
            self.time_stamps.pop(0)

        condition, color, suggestion = self.check_condition(value)
        self.label_value.setText(f"{value} mg/dL")
        self.label_value.setStyleSheet(f"color: {color}; font-size: 30px; font-weight: bold;")
        self.label_condition.setText(condition)
        self.label_condition.setStyleSheet(f"color: {color}; font-size: 18px;")
        self.label_time.setText(f"Time: {timestamp}")
        self.label_suggestion.setText(f"Suggestion: {suggestion}" if suggestion else "")

        if suggestion:
            self.speak(suggestion)

        max_history = 5
        if value < 70:
            self.low_history.append((timestamp, value))
            if len(self.low_history) > max_history:
                self.low_history.pop(0)
            self.recent_low.setText("🟥 Low:\n" + "\n".join([f"{v} mg/dL at {t}" for t, v in self.low_history]))
        elif 140 <= value < 180:
            self.high_history.append((timestamp, value))
            if len(self.high_history) > max_history:
                self.high_history.pop(0)
            self.recent_high.setText("🟧 High:\n" + "\n".join([f"{v} mg/dL at {t}" for t, v in self.high_history]))
        elif value >= 180:
            self.critical_history.append((timestamp, value))
            if len(self.critical_history) > max_history:
                self.critical_history.pop(0)
            self.recent_critical.setText("🔴 Critical:\n" + "\n".join([f"{v} mg/dL at {t}" for t, v in self.critical_history]))

        self.update_graph()

    def update_graph(self):
        self.ax.clear()
        self.ax.plot(self.time_stamps, self.blood_sugar_values, marker='o', linestyle='-', linewidth=2.5, color='#1f77b4')
        self.ax.fill_between(self.time_stamps, self.blood_sugar_values, color='#1f77b4', alpha=0.2)
        self.ax.set_title("📊 Blood Sugar Levels Over Time", fontsize=16, fontweight='bold', color='#2c3e50')
        self.ax.set_xlabel("Time", fontsize=12)
        self.ax.set_ylabel("Blood Sugar (mg/dL)", fontsize=12)
        self.ax.tick_params(axis='x', labelrotation=45, labelsize=9)
        self.ax.tick_params(axis='y', labelsize=10)
        self.ax.set_facecolor("#f9f9f9")
        self.ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
        self.ax.legend(["Blood Sugar (mg/dL)"], loc='upper right', fontsize=10)
        self.figure.tight_layout()
        self.canvas.draw()

    def save_to_csv(self):
        filename = "blood_sugar_data.csv"
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time", "Blood Sugar Level (mg/dL)"])
            for i in range(len(self.blood_sugar_values)):
                writer.writerow([self.time_stamps[i], self.blood_sugar_values[i]])

        QMessageBox.information(self, "Saved", "Data saved to blood_sugar_data.csv")
        self.status_label.setText("✅ Data saved to blood_sugar_data.csv")

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def toggle_chatbot(self):
        if self.chat_display.isVisible():
            self.chat_display.hide()
            self.chat_input.hide()
            self.chatbot_button.setText("💬 Open Chatbot")
        else:
            self.chat_display.show()
            self.chat_input.show()
            self.chatbot_button.setText("❌ Close Chatbot")
            self.chat_display.append("🩺 Chatbot: Hello! Ask me anything about blood sugar and health.")

    def handle_chat(self):
        question = self.chat_input.text().strip()
        if question:
            self.chat_display.append(f"🧑 You: {question}")
            answer = self.get_chatbot_response(question)
            self.chat_display.append(f"🩺 Chatbot: {answer}")
            self.chat_input.clear()

    def get_chatbot_response(self, question):
        question = question.lower()
        if "normal" in question:
            return "Normal blood sugar levels range from 70 to 140 mg/dL depending on timing and meals."
        elif "high" in question:
            return "High blood sugar could indicate diabetes or stress. Drink water and consult a doctor."
        elif "low" in question:
            return "Low blood sugar may cause dizziness or sweating. Eat or drink something sugary quickly."
        elif "prevent" in question:
            return "Maintain a healthy diet, exercise regularly, and monitor your levels to prevent complications."
        elif "diabetes" in question:
            return "Diabetes is a condition where the body cannot regulate blood sugar properly. Management is key."
        else:
            return "Sorry, I don't have an answer for that. Try asking about sugar levels, symptoms, or tips."


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BloodSugarMonitor()
    window.show()
    sys.exit(app.exec_())
