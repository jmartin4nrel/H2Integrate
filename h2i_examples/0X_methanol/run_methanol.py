from greenheart.core.greenheart_model import GreenHEARTModel


# Create a GreenHEART model
gh = GreenHEARTModel("0X_methanol.yaml")

# Run the model
gh.run()

gh.post_process()
