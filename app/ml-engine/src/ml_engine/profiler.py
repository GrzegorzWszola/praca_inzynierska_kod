from contextlib import contextmanager
from dataclasses import dataclass
import datetime as dt
from pathlib import Path
import time
import tracemalloc
import torch

@dataclass
class ProfilerRecord:
    model_name: str
    name: str
    elapsed: float
    current_kb: float
    peak_kb: float
    peak_vram: int

    def as_row(self):
        return self.model_name, self.name, self.elapsed, self.current_kb, self.peak_kb, self.peak_vram

    def as_dict(self):
        return {
            'model_name': self.model_name,
            "name": self.name,
            'elapsed': self.elapsed,
            'current_kb': self.current_kb,
            'peak_kb': self.peak_kb,
            'peak_vram': self.peak_vram
        }


class Profiler:
    def __init__(self, track_memory=True):
        self.track_memory = track_memory
        self.records: list[ProfilerRecord] = []

    @contextmanager
    def measure(self, name, model_name="Processing"):
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        tracemalloc.start()

        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            peak_vram = 0
            if torch.cuda.is_available():
                peak_vram = torch.cuda.max_memory_allocated()

            self.records.append(
                ProfilerRecord(
                    model_name=model_name,
                    name=name,
                    elapsed=elapsed,
                    current_kb=current / 1024,
                    peak_kb=peak / 1024,
                    peak_vram=peak_vram / (1024 ** 2),
                )
            )

    def reset(self):
        self.records.clear()

    def report(self):
        headers = ["Model Name", "Name", "Time [s]", "Current Memory [KB]", "Peak Memory", "Peak VRAM"]
        model_name_h, name_h, elapsed_h, current_h, peak_h, peak_vh = headers
        print(f"{model_name_h:<15}{name_h:<25}{elapsed_h:>15}{current_h:>20}{peak_h:>20}{peak_vh:>20}")

        for record in self.records:
            model_name, name, elapsed, current_kb, peak_kb, peak_vhm = record.as_row()
            print(f"{model_name:<15}{name:<25}{elapsed:>15.4f}{current_kb:>20.1f}{peak_kb:>20.1f}{peak_vhm:>20}")

        return [record.as_dict() for record in self.records]
