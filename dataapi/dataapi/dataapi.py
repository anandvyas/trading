import os 
import logging 
from abc import ABC, abstractmethod

class DATAAPI(ABC):
    
    def __init__(self) -> None:
        pass
    
    @abstractmethod
    def download(symbol, start="", end=""):
        pass