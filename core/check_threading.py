import queue
import threading
import time

maxsize = 1
input_queue = queue.Queue(maxsize=maxsize)
output_queue = queue.Queue(maxsize=maxsize)


def useless_function(seconds=20):
    output_queue.put("jojo")
    print(f'Waiting for {seconds} second(s)', end="\n")
    time.sleep(seconds)
    print(f'Done Waiting {seconds}  second(s)')


start = time.perf_counter()
t = threading.Thread(target=useless_function, args=[10])
t.start()
print(f'Active Threads: {threading.active_count()}')
print(output_queue.qsize())
time.sleep(5)
print(output_queue.get())
t.join()
end = time.perf_counter()
print(f'Finished in {round(end-start, 2)} second(s)')
