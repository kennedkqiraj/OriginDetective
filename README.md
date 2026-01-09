
# FTA Origin Determination Tool

## Overview

This repository contains a **Flask-based web application** designed to support **preferential origin determination** under **Free Trade Agreements (FTAs)**, with a current focus on the **EU–Vietnam Free Trade Agreement (EVFTA)**.

The tool automates a structured, rule-based workflow to assess whether a product qualifies as **originating** or **non-originating** based on:
- Product costing sheets
- Material origins
- Harmonized System (HS) codes
- Applicable FTA-specific thresholds and rules

The main goal of the project is to **reduce manual effort**, **increase consistency**, and **improve traceability** in origin determination decisions.

## Key Features

- Web-based interface for uploading product costing sheets (Excel / CSV)
- Automated **7-step origin determination workflow**
- Rule-based evaluation aligned with EVFTA requirements
- Transparent calculation of non-originating material percentages
- Clear final determination with intermediate analysis steps
- Modular architecture to support future trade agreements

## Supported Scope

- **Trade Agreement**: EU–Vietnam Free Trade Agreement (EVFTA)
- **Product Focus**: Footwear and parts (HS headings **6401–6406**)
- **File Formats**: `.xlsx`, `.xls`, `.csv`

## Application Architecture

The application follows a **service-oriented architecture**, separating data handling, business logic, and presentation.

### Web Framework
- Flask (core framework)
- Jinja2 templates
- Bootstrap (dark theme)

### Database Layer
- SQLAlchemy ORM
- Models:
  - AnalysisSession
  - MaterialAnalysis
- SQLite (development), PostgreSQL-ready

### File Processing
- Excel / CSV handling via pandas and openpyxl
- Flexible column mapping
- Input validation before processing

### Business Logic Services
- Origin Analyzer (7-step workflow)
- FTA Rules Engine (JSON-based)
- HS Code validation service

## Configuration

- FTA rules: `config/fta_rules.json`
- HS codes: `config/hs_codes.json`

## Project Structure

See repository tree for full layout.

## Running the Application

```bash
python app.py
```

The application runs at `http://127.0.0.1:5000`.

## Intended Use

This project is intended for **research, prototyping, and internal decision support**.  
It does **not** replace official customs rulings.

## Extensibility

The system is designed to support:
- Additional FTAs
- Extended HS code coverage
- Rule updates via configuration

## License

License information can be added as required.
