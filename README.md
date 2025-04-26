# Hosting Capacity Analysis of EV Charging Stations in Distribution Networks

This repository contains all the Python scripts developed for the undergraduate thesis:

**"Analysis of the Hosting Capacity of the Distribution Network with the Implementation of Electric Vehicle Charging Stations"**

The study explores the integration of electric vehicle (EV) charging stations in medium- and low-voltage distribution networks, using modeling and simulation tools based on BDGD and DSS frameworks.

## 🧠 Project Summary

The increasing penetration of electric vehicles presents a new challenge for distribution networks. This work evaluates how much EV charging load can be hosted without violating operational limits, such as voltage levels and transformer capacities.

The simulations are based on:

- Real distribution network data from the [BDGD - Brazilian Distribution Grid Database](https://bdgd.iberd.org/)
- Electrical behavior modeled using [OpenDSS](https://sourceforge.net/projects/electricdss/) through `dss_python` bindings
- Custom Python scripts for automation, analysis, and visualization

## ⚙️ Features

- 🏗️ Automated setup of BDGD network models  
- 🔌 EV load profile simulation with concurrency and randomness parameters  
- 📉 Hosting capacity analysis based on DSS voltage and current limits  
- 📊 Visualization tools for plotting voltage drops, transformer loading, etc.


📚 Academic Reference
If you use this code in your research or academic work, please cite the original thesis:

[Bruno Dambroski Serafini]
Analysis of the Hosting Capacity of the Distribution Network with the Implementation of Electric Vehicle Charging Stations.
Bachelor's Thesis, [Universidade Federal de Mato Grosso], 2025.
