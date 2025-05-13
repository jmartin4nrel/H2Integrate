from h2integrate.core.h2integrate_model import H2IntegrateModel


# Create an H2I model - comment out one line to select SMR or CO2 hydrogenation
h2i = H2IntegrateModel("03_smr_methanol.yaml")
h2i = H2IntegrateModel("03_co2h_methanol.yaml")

# Run the model
h2i.run()

h2i.post_process()
