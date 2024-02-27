
## Installation Instructions

Follow these steps to set up the environment and run the application on Ubuntu 22.04.

### Prerequisites

Before you begin, ensure you have Python installed on your system. This project requires Python 3.8 or higher. You can check your Python version by running:

sh
python3 --version


If Python is not installed, you can install it using the following command:

sh
sudo apt update
sudo apt install python3 python3-venv python3-pip


### Step 1: Create a Python Virtual Environment

A virtual environment is a tool that helps to keep dependencies required by different projects separate. Create a virtual environment by running:

sh
python3 -m venv .venv


### Step 2: Activate the Virtual Environment

Once you have created a virtual environment, you need to activate it:

sh
source .venv/bin/activate


You should now see `(.venv)` at the beginning of your terminal prompt indicating that you are working inside the virtual environment.

### Step 3: Install Required Python Packages

Install all the required packages using `pip`. The `requirements.txt` file should list all Python libraries that your project depends on.

sh
pip install -r requirements.txt


Make sure your `requirements.txt` file is in the same directory where you run this command.

### Step 4: Install MongoDB

MongoDB is a NoSQL database that you'll need to install. You can install MongoDB with the following commands:

sh
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org


After installation, start the MongoDB service and enable it to start on boot with the following commands:

sh
sudo systemctl start mongod
sudo systemctl enable mongod


### Step 5: Install Google Chrome and ChromeDriver

To use Selenium with Google Chrome, you need to install Google Chrome and the ChromeDriver.

1. Install Google Chrome:

sh
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb


2. Install ChromeDriver:

First, check the version of Google Chrome:

sh
google-chrome --version


Then, download the corresponding version of ChromeDriver from the [ChromeDriver download page](https://sites.google.com/chromium.org/driver/). Make sure to replace `XX` with the correct version number in the URL below:

sh
wget https://chromedriver.storage.googleapis.com/XX.XX.XXX.X/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chown root:root /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver


### Step 6: Verify the Installation

After completing the above steps, verify that everything is installed correctly:

1. Check the Python packages:

sh
pip freeze


2. Check MongoDB status:

sh
sudo systemctl status mongod


3. Check Chrome and ChromeDriver:

sh
google-chrome --version
chromedriver --version


You should see the versions of Google Chrome and ChromeDriver printed on the terminal.
