# LARCO: Household Laundry Appliance Resource Consumption and Operation Dataset

![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18657997.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg) 
![Maintenance](https://img.shields.io/maintenance/yes/2026)
![Dataset size](https://img.shields.io/badge/size-36GB-blue)
![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)

## License
The dataset is licensed under the [Creative Commons Attribution 4.0 International (CC-BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
You are free to share and adapt the material for any purpose, even commercially, as long as you give appropriate credit.

## Contacts
For any questions please contact zjasiunas (at) fc.ul.pt

## Overview
Household laundry appliances (washing machines, tumble dryers) are significant contributors to residential energy consumption. While energy labels provide standardized efficiency values, **actual performance strongly depends on user behavior and operating conditions**.

The **LARCO dataset** provides a unique, open-access resource containing multivariate time-series measurements of laundry appliances under both **laboratory-controlled** and **real-world household** conditions.

Data include:
- Energy consumption (current, voltage, power, frequency, power factor)
- Water consumption and flow
- Appliance internal/external temperatures
- Humidity and ambient conditions
- Vibration and audio (lab setting only)

Aggregated metadata:
- Experiment identifiers (timestamp, unique cycle ID)
- File info (file path, file name, link to energy performance file)
- Appliance details (type, brand, model, state – new or faulty, combined name)
- Operational info (program name, heat setting, RPM, cycle name, duration)
- Environment (lab, household, or experimental; AC setting; ambient temperature)
- Load info (target load, actual dry load weight, post-cycle wet weight)
- Lab-specific data (position ID in laboratory setup)
- Data quality flags (accelerometer/audio availability, missing values indicator)
  
Outsource data:
- Weather data (outdoor temperature, humidity, and atmospheric pressure from OpenWeatherMap)

LARCO supports research on:
- Appliance efficiency assessment  
- User behaviour modelling  
- Intrusive load monitoring (ILM)
- Non-intrusive load monitoring (NILM)  
- Personalised energy feedback systems  
- Sustainable energy use and demand-side management  

Dataset DOI: https://doi.org/10.5281/zenodo.18657997

---

## Dataset Structure

The dataset is organised into three main modalities.  
Each observation may include up to three parallel data streams:

1. **General data** — energy, environmental, and operational measurements  
2. **Vibration data** — accelerometer recordings  
3. **Audio data** — laboratory microphone recordings  

These are distributed as separate ZIP archives:

---

### `general.zip`
Contains the main 1 Hz sensor data from three environments:

- **laboratory**: Controlled experiments at 16 °C, 25 °C, and 31 °C with systematic variation of load sizes (0 kg up to maximum capacity –1 kg) and washing/drying programmes.  
- **household**: Real-world monitoring of 15 appliances across 10 homes (2004–2020), capturing natural variability in use.  
- **exploratory**: Early recordings for testing and validation.  

---

### `vibrations.zip`
Contains all accelerometer sensor files (200 Hz), from two environments:

- **Laboratory**  
- **Household**  

---

### `audio.zip`
Contains all audio recordings (11 kHz) from the **laboratory** environment.  

⚠️ **Note:** The original WAV files were compressed using FLAC.  
To convert them back to WAV, run:

```bash
find audio -type f -name "*.flac" -exec flac -d {} \;
```

Each laboratory experiment contains:
- `device_brand_model_environemnt-temp_program_temperature_laundry-laod.csv`: 1Hz operational/environmental data  
- `device_brand_model_environemnt-temp_program_temperature_acc.parquet`: 200Hz vibration data (top/side/back)  
- `device_brand_model_environemnt-temp_program_temperature.wav`: 11kHz sound (lab only, privacy-safe, not all appliances, audio)
- `brand_model_metadata.csv`: Appliance characteristics 

Each household experiment contains:
- `device_brand_model_timestamp.csv`: 1Hz operational/environmental data  
- `device_brand_model_timestamp.parquet`: 200Hz vibration data (top/side/back)  
- `brand_model_metadata.csv`: Appliance characteristics

Each experimental record contains:
- `device_brand_model_program_temperature_laundry-load.csv`: 1Hz operational/environmental data  
- `brand_model_metadata.csv`: Appliance characteristics 
---

## How to Use
1. Download dataset from Zenodo: [Zenodo DOI link]
2. Unpack `general.zip`, (optionally) `vibrations.zip` and `audio.zip` (all archives contain same metadata.xlsx file)
3. Use the provided Jupyter notebooks in `scripts/quick start` to explore and analyse

## Folder structure
All unpacked zip files can be placed in a folder with the name of your choice. The structure should be the following:

```text
LARCO/                          # main folder
├── acc/                        # from `vibrations.zip`
│   ├── laboratory/
│   └── household/
├── audio/                      # from `audio.zip`
│   └── washing machine/
├── household/                  # from `general.zip`
├── laboratory/                 # from `general.zip`
├── exploratory_stage/          # from `general.zip`
├── aggregated_data.csv         # combined dataset (all modalities)
├── aggregated_data_acc.csv     # aggregated accelerometer data
├── weather_data.csv            # external weather data
├── aggregated_data_audio.csv   # aggregated audio data
└── metadata.xlsx               # sensor models, description of use, units, frequencies
```

All the example files from this repository should be placed in the main folder. 

## Recorded Features

The dataset includes synchronized timeseries measurements across three environments: **Laboratory (L)**, **Household (H)**, and **Experimental (E)**.  

### 1. Energy Use
| Feature       | Unit | Environments |
|---------------|------|--------------|
| Voltage       | V    | L / H        |
| Current       | A    | L / H        |
| Power         | W    | L / H / E    |
| Power factor  | pf   | L / H        |
| Frequency     | Hz   | L / H        |

### 2. Indoor Environment
| Feature            | Unit | Environments |
|--------------------|------|--------------|
| Ambient temperature| °C   | L / H        |
| Relative humidity  | %    | L / H        |

### 3. Water System (washing machines)
| Feature                | Unit | Environments |
|------------------------|------|--------------|
| Inlet water volume     | mL   | L / H / E    |
| Outlet water volume    | mL   | L only       |
| Inlet water temperature| °C   | L / H        |
| Outlet water temperature| °C  | L / H        |
| Water pressure         | psi  | L / H        |

### 4. Appliance-Specific Sensors
| Appliance        | Feature           | Unit | Environment |
|------------------|-------------------|------|-------------|
| Washing machine  | Drum temperature  | °C   | L only      |
| Washing machine  | Door temperature  | °C   | L only      |
| Dryer            | Lint trap temperature (2x) | °C | L only |

### 5. Additional Modalities
| Feature         | Details                                    | Environments |
|-----------------|--------------------------------------------|--------------|
| Vibration       | 3D accelerometer (top, side, back), 200 Hz | L / H        |
| Audio           | Pickup microphone, 11 kHz                  | L only       |
| Load weights    | Dry/wet load, pre/post cycle (±0.001 kg)   | L / E        |
| Dryer tank water| Volume collected (±0.001 L)                | L only       |
| Cycle metadata  | Program name, heating level, RPM, duration | L / E        |

---

## Helper Tools and Example Workflows

To support exploration and analysis of the dataset, we provide several Jupyter notebooks and Python scripts.  
These examples demonstrate how to load, process, and analyse different data modalities.

### 🔹 Data Loading
- **`read_main_data.ipynb`** — Load and explore 1 Hz operational/environmental data.  
- **`read_acc_data.ipynb`** — Read and process vibration data (200 Hz accelerometer).  
- **`read_audio_data.ipynb`** — Access and inspect audio data (11 kHz, FLAC-compressed).  

### 🔹 Preprocessing and Statistics
- **`count_missing_data.ipynb`** — Identify and quantify missing values across files.  
- **`calculate_extra_statistics.ipynb`** — Compute additional cycle-level metrics.  
- **`auto_water_heating_label.ipynb`** — Automatic annotation of water heating events.  

### 🔹 Feature Extraction
- **`extract_frequencies_from_accelerometer.py`** — Frequency-domain features from vibration data.  
- **`extract_frequencies_from_audio.ipynb`** — Spectral features from audio data.  

### 🔹 Annotation and Utility
- **`manual_annotation.py`** — Interactive tool for manual event labeling.  
- **`listen_audio_file.py`** — Simple script to play back audio samples.  

---

## Quick Start

1. Install dependencies (Python ≥3.9 recommended):  
   ```bash
   pip install -r requirements.txt
   
