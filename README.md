# IN_AllenCounty
US County Tax Automation – Allen County (Indiana)
Selenium + Python | Raw Text | JSON Output | Dataset Creation | Production Workflow

This repository demonstrates a complete end-to-end automation workflow for one US county (Allen County, Indiana).
It follows the same architecture and logic I use in my real project where I have built:
400+ automation scripts
100+ US counties automated

Full pipeline: Raw Text → JSON Output → Dataset → Production Script

This project is a mini version of the real production system.

Project Structure
My_Project/
│
├── env/                     # Environment setup, configurations
│
├── Scripts/
│   ├── Testing_Script.py    # Validate automation for one name/address
│   ├── Raw_Text_Script.py   # Extract raw text for multiple records
│   ├── Output_Script.py     # Convert raw text → formatted JSON output
│   ├── Dataset_Script.py    # Build datasets (raw text + output)
│   └── Production_Script.py # End-to-end production-ready automation
│
└── Final_Result/
    ├── Raw_Text_Result.json
    ├── Output_Result.json
    ├── Dataset_Result.json
    └── Testing_Script_Result.json

Scripts Overview
1. Testing_Script.py
Runs automation for one owner name + address to confirm correct record matching and extraction.

2. Raw_Text_Script.py
Handles multiple records in batch and extracts raw tax/property text for each one.

3. Output_Script.py
Converts raw text into structured JSON used in my company’s internal UI (same structure as UiPath output).

4. Dataset_Script.py
Generates training-ready datasets combining raw text + JSON output
(based on format provided by Data Analysts).

5. Production_Script.py
A complete production-ready pipeline inside one script.
Running this = same result as Testing Script but in scalable, reusable form.

Final Output Files
1.Raw_Text_Result.json
Raw text extracted from county website.

2.Output_Result.json
Formatted JSON output generated from raw text.

3.Dataset_Result.json
Dataset combining raw text + output (used for Machine Learning / training).

4.Testing_Script_Result.json
Single-record raw text output used for validation.

Tech Stack
1.Python
2.Selenium WebDriver
3.JSON
4.Git / GitHub

How to Run the Project
1.Install dependencies
pip install -r requirements.txt

2.Run testing script (single record)
python Scripts/Testing_Script.py

3.Run raw text extraction
python Scripts/Raw_Text_Script.py

4.Generate output JSON
python Scripts/Output_Script.py

5.Generate dataset
python Scripts/Dataset_Script.py

6.Run production workflow
python Scripts/Production_Script.py

About This Project:

This repository is a sample demonstration of my work in:
Automating county tax portals
Extracting raw text
Formatting tax data into structured JSON
Creating datasets
Building production-ready scripts

The same design is used across my real-world automation of:
100+ US counties
400++ scripts (raw text, output, dataset, production)

Author:
Ramya Sandhiveeran
Python Automation Engineer | RPA Developer
ramyasandhiveeranofficial@gmail.com
