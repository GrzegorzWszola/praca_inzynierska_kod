from enum import Enum

from sqlmodel import Field, SQLModel

class EmotionLabel(str, Enum):
    JOY = "joy"                     
    SADNESS = "sadness"           
    TENSE = "tense"             
    CALM = "calm"                     
    NEUTRAL = "neutral"           

