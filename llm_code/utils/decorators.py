import time
from functools import wraps

def time_checker(func):
    @wraps(func)
    def time_counter(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        total_time = end_time - start_time
        
        # Human-readable formatting
        minutes, seconds = divmod(total_time, 60)
        if minutes > 0:
            time_str = f"{int(minutes)} min {seconds:.0f} sec"
        else:
            time_str = f"{seconds:.2f} sec"
        
        print(f"Execution Time: {time_str}")
        return result
    return time_counter