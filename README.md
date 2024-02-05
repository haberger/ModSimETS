# Modelling and Simulation Project - European Trading System 
This is the code repository of the project "Modeling the price dynamics of CO2 emission allowances" for the course "Modelling and Simulation" at TU Wien. It aims to model the price dynamics of CO2 emission allowances in the European Trading System (ETS) using agent-based modeling and simulation.

## Setting up the environment
We use conda to manage the environment. To create the environment, run the following command in the terminal:

```bash
conda env create -f env.yml
```

To activate the environment, run the following command in the terminal:

```bash
conda activate modsim
```

## Repository structure
The repository is structured as follows:
- ```data```: contains the data used for the analysis and for initializing the agents of the EU model.
- ```CompanyAgent.py```: implementation of the agent representing a company in the EU ETS.
- ```Environment.py```: implementation of the environment, which models the market behavior. 
- ```modsim.ipynb```: Jupyter notebook containing the simulation code and results.

## Running the code
To run the simulation execute the ```modsim.ipynb``` notebook. Make sure to choose the correct kernel (```modsim```) when running the notebook.

