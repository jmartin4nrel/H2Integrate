from greenheart.core.greenheart_model import GreenHEARTModel


# Create a GreenHEART model
gh = GreenHEARTModel("02_texas_ammonia.yaml")

# Run the model
gh.run()

gh.post_process()
