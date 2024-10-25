# Examples Overview

This directory provides example Jupyter notebooks demonstrating how to use the GreenHEART tool for technoeconomic analysis of green technology applications. These workflows and calculations cover hydrogen production, steel manufacturing, ammonia synthesis, and Proton Exchange Membrane (PEM) electrolyzer modeling. GreenHEART enables co-design and simulation of an integrated renewable energy and hydrogen production plant, along with optional end-use applications.

The first three notebooks focus on the GreenHEART simulation interface, which supports single analysis cases as well as optimization for levelized cost of product. The final example, `04-PEM_electrolyzer.ipynb`, illustrates how to use GreenHEART's PEM electrolyzer model.

> **Note**: The `reference_plants` directory, containing reference designs for green hydrogen, ammonia, and steel plants across the U.S., will be removed in future releases. Reference plant data is now hosted at [NREL/ReferenceHybridSystemDesigns](https://github.com/NREL/ReferenceHybridSystemDesigns).

## Structure

- **01-green-hydrogen.ipynb**: Demonstrates a workflow for green hydrogen production using renewable energy and electrolysis.
- **02-green-steel.ipynb**: Illustrates green steel production using hydrogen as a reducing agent via hydrogen direct reduced iron and electric arc furnace (HDRI-EAF) technology.
- **03-green-ammonia.ipynb**: Covers green ammonia production through renewable hydrogen in the Haber-Bosch process.
- **04-PEM_electrolyzer.ipynb**: Details the use of the GreenHEART PEM Water Electrolyzer model, including key components and operation.

## Quick Start

1. Clone the repository: `git clone https://github.com/GreenHEART.git`
2. Follow the setup instructions in the main `README.md`
3. Install the example dependencies:

   ```bash
   pip install ".[examples]"
   ```