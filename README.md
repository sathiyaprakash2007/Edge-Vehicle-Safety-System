# 🚗 Edge Vehicle Safety System

An AI-powered vehicle safety monitoring system built with **Python, Computer Vision, YOLO, and Streamlit**. The system analyzes video input in real time to detect vehicles and identify potential safety-related situations.

## 📌 Project Overview

The **Edge Vehicle Safety System** is designed to demonstrate how Artificial Intelligence and Computer Vision can be used for real-time vehicle monitoring.

The application processes video input, detects vehicles using an AI-based object detection model, and provides safety-related monitoring through an interactive Streamlit interface.

## ✨ Features

* 🚘 Real-time vehicle detection
* 🎯 AI-based object detection using YOLO
* 📹 Video processing and analysis
* 🖥️ Interactive Streamlit web interface
* 🔔 Safety monitoring and alerts
* 📊 Detection results and status information
* ⚡ Designed for real-time/edge-based processing

## 🛠️ Technologies Used

| Technology                | Purpose                          |
| ------------------------- | -------------------------------- |
| **Python**                | Core programming language        |
| **Streamlit**             | Web application interface        |
| **OpenCV**                | Video and image processing       |
| **YOLO / Ultralytics**    | Object detection                 |
| **NumPy**                 | Numerical and array operations   |
| **Computer Vision**       | Vehicle detection and monitoring |
| **AI / Machine Learning** | Intelligent safety analysis      |

## 📂 Project Structure

```text
edge_vehicle_safety_smooth/
│
├── app.py
├── requirements.txt
├── README.md
│
├── detection/
│   └── detector.py
│
├── models/
│   └── [model files]
│
├── utils/
│   └── [utility files]
│
└── .gitignore
```

> The exact structure may vary depending on the files included in the project.

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/edge-vehicle-safety.git
```

### 2. Navigate to the project directory

```bash
cd edge-vehicle-safety
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
.venv\Scripts\activate
```

### 5. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## ▶️ Run the Application

Start the Streamlit application:

```bash
python -m streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

Open the URL in your web browser.

## 🧠 How It Works

```text
Video / Camera Input
        ↓
Frame Processing
        ↓
YOLO Object Detection
        ↓
Vehicle Detection
        ↓
Safety Analysis
        ↓
Alerts / Results
        ↓
Streamlit Dashboard
```

The application continuously processes video frames and uses the object detection model to identify vehicles. The detection results are then analyzed and displayed through the Streamlit interface.

## 🎯 Use Cases

The system can be extended for applications such as:

* Vehicle monitoring
* Road safety analysis
* Traffic surveillance
* Driver assistance systems
* Accident-risk monitoring
* Smart transportation systems
* AI-based safety applications

## 🚀 Future Improvements

Possible improvements include:

* Integration with CCTV cameras
* Improved vehicle tracking
* License plate detection
* Speed estimation
* Collision-risk prediction
* Lane detection
* Driver behavior monitoring
* Cloud-based monitoring
* Mobile notifications
* Edge-device deployment using Raspberry Pi or NVIDIA Jetson

## 📸 Screenshots

Add screenshots of your application here.

Example:

```markdown
![Application Screenshot](screenshots/dashboard.png)
```

You can create a `screenshots` folder and place your project screenshots inside it.

## 🔒 Security & Privacy

Do not commit sensitive information such as:

* API keys
* Passwords
* Database credentials
* `.env` files
* Private configuration files

Use environment variables for sensitive configuration.

## 📋 Requirements

The required Python packages are listed in:

```text
requirements.txt
```

Install them using:

```bash
python -m pip install -r requirements.txt
```

## 👨‍💻 Developer

**Sathiyaprakash M**

Computer Science and Engineering (AI & ML) Student
Aspiring Full Stack Developer

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

## 📄 License

This project is created for **educational and project-development purposes**.

---

### 🔗 Project Repository

GitHub: `https://github.com/YOUR_USERNAME/edge-vehicle-safety`
