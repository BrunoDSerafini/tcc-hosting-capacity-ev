# Hosting Capacity Analysis of EV Charging Stations in Distribution Networks

This repository contains all the Python scripts developed for the undergraduate thesis:

**"Analysis of the Hosting Capacity of the Distribution Network with the Implementation of Electric Vehicle Charging Stations"**

The study explores the integration of electric vehicle (EV) charging stations in medium- and low-voltage distribution networks, using modeling and simulation tools based on BDGD and DSS frameworks.

## 🧠 Project Summary

The increasing penetration of electric vehicles presents a new challenge for distribution networks. This work evaluates how much EV charging load can be hosted without violating operational limits, such as voltage levels and transformer capacities.

The simulations are based on:

- Real distribution network data from the [BDGD - Brazilian Distribution Grid Database](https://dadosabertos.aneel.gov.br/dataset/base-de-dados-geografica-da-distribuidora-bdgd)
- Electrical behavior modeled using [OpenDSS](https://sourceforge.net/projects/electricdss/) through `dss_python` bindings
- py_dss_interface from Radatz, P. (2025). [py-dss-interface: A Python package that interfaces with OpenDSS powered by EPRI (Version X.X.X) Computer software. GitHub]( https://github.com/PauloRadatz/py_dss_interface)
- Custom Python scripts for automation, analysis, and visualization

## ⚙️ Features

- 🏗️ Automated setup of BDGD network models  
- 🔌 EV load profile simulation with concurrency and randomness parameters  
- 📉 Hosting capacity analysis based on DSS voltage and current limits  
- 📊 Visualization tools for plotting voltage drops, transformer loading, etc.


📚 Academic Reference
If you use this code in your research or academic work, please cite the original thesis:

📚 How to Cite
If you use this repository or any part of it in your academic work, please reference it as follows:

APA Style:
Serafini, B. D. (2025). Analysis of the Hosting Capacity of the Distribution Network with the Implementation of Electric Vehicle Charging Stations (Bachelor's thesis). Universidade Federal de Mato Grosso.

BibTeX Entry:


```bibtex
@thesis{serafini2025hostingcapacity,
  author = {Bruno Dambroski Serafini},
  title = {Analysis of the Hosting Capacity of the Distribution Network with the Implementation of Electric Vehicle Charging Stations},
  year = {2025},
  school = {Universidade Federal de Mato Grosso},
  type = {Bachelor's Thesis}
}
