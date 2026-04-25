import yaml
import time

class APIKeyManager:
    def __init__(self, keys, rate_limit=600, window_seconds=300):
        self.keys = keys
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.usage = {k: [] for k in keys}  # timestamps of requests per key
        self.index = 0

    def get_key(self):
        now = time.time()
        for _ in range(len(self.keys)):
            key = self.keys[self.index]
            # Remove timestamps outside the window
            self.usage[key] = [t for t in self.usage[key] if now - t < self.window_seconds]
            if len(self.usage[key]) < self.rate_limit:
                self.usage[key].append(now)
                self.index = (self.index + 1) % len(self.keys)
                return key
            self.index = (self.index + 1) % len(self.keys)
        # If all keys are exhausted, wait for the soonest available
        soonest = min(min(times) for times in self.usage.values() if times)
        wait = self.window_seconds - (now - soonest)
        print(f"All API keys exhausted, waiting {wait:.1f}s...")
        time.sleep(max(wait, 1))
        return self.get_key()
