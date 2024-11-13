import numpy as np

# Define the function for the given equation with detailed comments for each variable
def calc_pre_and_winning_costs(T, P, p, z, F, j, A, e, M, Q, V, N):
    """
    Calculates the total direct capital cost (C) in 2018 US dollars.

    From:
    Estimating the Capital Costs of Electrowinning Processes
    Caspar Stinn and Antoine Allanore 2020 Electrochem. Soc. Interface 29 44
    https://iopscience.iop.org/article/10.1149/2.F06202IF

    Parameters:
    - T : float : Electrolysis temperature, °C
    - P : float : Pressure, assumed unit for this context
    - p : float : Relevant process parameter for the conventional chemical engineering scaling law
    - z : int   : Moles of electrons reacting to produce a mole of product
    - F : float : Magnitude of electric charge per mole of electrons, coulombs per mole (C/mol)
    - j : float : Current density, A/m²
    - A : float : Electrode (cathode) area, m²
    - e : float : Current efficiency (dimensionless, between 0 and 1)
    - M : float : Electrolysis product molar mass, kg/mol
    - Q : float : Installed power capacity, MW
    - V : float : Cell operating voltage, V
    - N : int   : Number of rectifier lines

    Returns:
    - C : float : Total direct capital cost in 2018 US dollars
    """

    # Constants in the equation
    term1 = 51010. / (1 + np.exp(-3.823e-3 * (T - 631)))
    term2 = 5634000. / (1 + np.exp(-7.813e-3 * (T - 349)))
    
    # Electrolysis and product handling contribution to the total cost
    # ( (p * z * F) / (j * A * e * M) )^0.9
    electrolysis_product_handling = ( (p * z * F) / (j * A * e * M) )**0.9
    
    # Power rectifying contribution
    # 750000 * Q * V^0.15 * N^0.5
    power_rectifying_contribution = 750000 * Q * V**0.15 * N**0.5

    print(term1, term2, electrolysis_product_handling, power_rectifying_contribution)

    pre_costs = term1 * P**0.8
    electrowinning_costs = term2 * electrolysis_product_handling + power_rectifying_contribution

    return pre_costs, electrowinning_costs

# Example values for each variable (replace with actual values)
T = 1000.   # Temperature in °C, example value
P = 1.5     # Pressure, example value
p = 1.      # Total production rate, kg/s
z = 3       # Moles of electrons per mole of product, example value
F = 96485   # Electric charge per mole of electrons (Faraday constant), C/mol
j = 5000    # Current density, A/m², example value
A = 30.     # Electrode area, m², example value
e = 0.95    # Current efficiency (dimensionless), example value
M = 0.018   # Electrolysis product molar mass, kg/mol (e.g., water)
Q = 500.    # Installed power capacity, MW, example value
V = 4.18    # Cell operating voltage, V, example value
N = 3       # Number of rectifier lines, example value

# Calculate C
pre_costs, electrowinning_costs = calc_pre_and_winning_costs(T, P, p, z, F, j, A, e, M, Q, V, N)
print('Total direct capital cost (C) in 2018 US M dollars:', (pre_costs + electrowinning_costs) / 1.e6)
print('Pre-electrowinning costs:', pre_costs)
print('Electrowinning costs:', electrowinning_costs)
