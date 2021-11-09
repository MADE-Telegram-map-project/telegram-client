import threading
import time


def useless_function(seconds):
    print(f'Waiting for {seconds} second(s)', end="\n")
    time.sleep(seconds)
    print(f'Done Waiting {seconds}  second(s)')


start = time.perf_counter()
t = threading.Thread(target=useless_function, args=[1])
t.start()
print(f'Active Threads: {threading.active_count()}')
t.join()
end = time.perf_counter()
print(f'Finished in {round(end-start, 2)} second(s)')
