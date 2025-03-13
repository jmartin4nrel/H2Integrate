from greenheart.core.greenheart_model import GreenHEARTModel


# Create a GreenHEART model
gh = GreenHEARTModel("08_onshore_steel_mn.yaml")

# Run the model
gh.run()

gh.post_process()
