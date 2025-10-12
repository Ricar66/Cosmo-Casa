APPLICATION LINK : https://cosmocasa-hnfkehembzgybjeh.canadacentral-01.azurewebsites.net/

🚀 Cosmo-Casa: A Space Mission Habitat Simulator
Cosmo-Casa is an educational, gamified web application designed to teach students about the engineering, logistics, and critical decisions involved in planning a space mission and building a sustainable habitat on the Moon, Mars, or an exoplanet.

Built for the NASA Space Apps Challenge, this project bridges the gap between classroom learning and real-world space exploration challenges, making complex topics accessible and engaging for both students and teachers.

✨ About The Project
This simulator provides a hands-on experience where users must make crucial trade-offs regarding payload mass, energy consumption, and life support systems. The project is built with a simple yet robust architecture using Flask and SQLite, ensuring it is lightweight and easy to run.

Two Core Profiles:
🧑‍🏫 Teacher (Admin): Manages virtual classrooms, customizes mission parameters (destination, spacecraft), creates learning challenges, and tracks student progress via a comprehensive dashboard.

🧑‍🚀 Student: Joins a mission with a unique code, designs their habitat by selecting from a catalog of modules, and launches a turn-based simulation where their choices are tested against random events like solar storms and micrometeoroid impacts.

🛠️ Key Features
Interactive Habitat Editor: A 2D/3D drag-and-drop interface for designing and building the habitat.

Realistic Mission Simulation: A turn-based journey where module selection directly impacts the outcome against random events.

Teacher Dashboard: Full control over classrooms, student lists, challenges, and results.

Data Export: Teachers can export student data and answers to a CSV file for grading.

Gamified Learning: Students learn about real-world engineering constraints (mass, power, life support) in an engaging way.

Lightweight & Accessible: Built with Flask + SQLite, it requires no complex database setup.

⚙️ Getting Started
Follow these instructions to get a local copy up and running.

Prerequisites
Python 3.10+

pip (Python package installer)

Installation & Execution
Clone the repository (or download the source code):

Bash

git clone https://your-repository-url.com/Cosmo-Casa.git
cd Cosmo-Casa
Create and activate a virtual environment:

Windows (PowerShell):

PowerShell

python -m venv .venv
.venv\Scripts\Activate.ps1
Linux / macOS:

Bash

python -m venv .venv
source .venv/bin/activate
Install the dependencies:

Bash

pip install -r requirements.txt
Run the application:
You may need to run two servers simultaneously for real-time features.

Terminal 1 (Real-time Simulation Server):

Bash

python websocket_server.py
Terminal 2 (Main Web Server):

Bash

python app.py

🖥️ Usage
Once the servers are running, you can access the application in your web browser.

Teacher Access
Navigate to the teacher dashboard: http://localhost:5000/professor/dashboard

Log in with the default credentials:

Username: admin

Password: 123456

From the dashboard, you can create classrooms (salas), upload student lists (.txt), and define mission parameters.

Student Access
Students go to the main page: http://localhost:5000

They enter the Room Code provided by the teacher and their full name as it appears on the teacher's list.

They can then proceed with the mission simulation and habitat construction.

🗺️ Project Roadmap
[ ] 3D Habitat Editor: Transition from the 2D editor to a fully interactive 3D environment using Three.js.

[ ] NASA API Integration: Use real-time data from NASA APIs (e.g., space weather, Mars rover images) to enhance simulation realism.

[ ] Shared Challenge Bank: Allow teachers to create and share challenges with tags (e.g., Physics, Biology, Engineering).

[ ] Enhanced Metrics Panel: Add visual charts and graphs to the teacher dashboard for better analytics on student performance.

[ ] Unit Testing: Implement a testing suite for critical backend logic in services/db.py and the routes.

🤝 Contributing
Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request
