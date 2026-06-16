from abc import ABC, abstractmethod


class Converter(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def convert(self, input_path: str, output_dir: str) -> str:
        raise NotImplementedError()
