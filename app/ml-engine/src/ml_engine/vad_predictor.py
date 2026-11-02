from pathlib import Path


class VadPredictor:
    def __init__(self):
        self.model = None
        

    def load_model(self, input: str):
        input_path = Path(input)

        
