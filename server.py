import socket
import threading
import pickle
import heapq
import os
import struct
import time

# Import trust manager functions
from utils.trust_manager import get_trust_score, update_trust_score, all_trust_scores, initialize_trust_score

# Simple logger implementation if the original is missing
def log_event(message):
    print(f"[LOG] {message}")

HOST = '0.0.0.0'
PORT = 5000
DATASET_PATH = 'data/uniform.txt'
SORTED_OUTPUT_FILE = "data/sorted_data.txt"
CHUNK_LOCK = threading.Lock()
SORTED_CHUNKS = []
CONNECTED_WORKERS = []

def recv_all(sock, length):
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            raise EOFError("Socket closed before full message received")
        data += more
    return data

def load_dataset(file_path):
    with open(file_path, "r") as f:
        data = [float(line.strip()) for line in f.readlines()]
    return data

def save_sorted_data(sorted_data):
    with open(SORTED_OUTPUT_FILE, "w") as f:
        f.write("\n".join(map(str, sorted_data)))
        print(f"[INFO] Sorted data saved to {SORTED_OUTPUT_FILE}")

def divide_chunks(data, trust_scores):
    # Ensure all workers have a positive score to avoid division by zero
    for ip in trust_scores:
        if trust_scores[ip] <= 0:
            trust_scores[ip] = 1
    
    total_score = sum(trust_scores.values())
    chunks = []
    start = 0
    
    # Sort trust_scores by IP to ensure consistent ordering
    sorted_scores = dict(sorted(trust_scores.items()))
    
    for ip, score in sorted_scores.items():
        length = max(int(len(data) * score / total_score), 1)  # Ensure at least 1 element
        chunk = data[start:start+length]
        chunks.append((ip, chunk))
        start += length
    
    # Handle any leftover data
    if start < len(data):
        chunks[-1] = (chunks[-1][0], chunks[-1][1] + data[start:])
    
    return chunks

def handle_worker(conn, addr):
    worker_ip = addr[0]
    print(f"[INFO] Worker {worker_ip} connected.")

    # Initialize trust if new IP
    initialize_trust_score(worker_ip)
    CONNECTED_WORKERS.append((conn, worker_ip))

def worker_task(conn, ip, chunk):
    try:
        # Send chunk to worker
        data_to_send = pickle.dumps(chunk)
        conn.sendall(struct.pack('>I', len(data_to_send)))
        conn.sendall(data_to_send)
        print(f"[INFO] Sent {len(chunk)} values to {ip}")

        # Receive sorted chunk from worker
        raw_len = recv_all(conn, 4)
        msg_len = struct.unpack('>I', raw_len)[0]
        sorted_data = recv_all(conn, msg_len)
        sorted_chunk = pickle.loads(sorted_data)

        with CHUNK_LOCK:
            SORTED_CHUNKS.append(sorted_chunk)
            update_trust_score(ip, success=True)
            log_event(f"Worker {ip} completed successfully. Updated trust score.")

        print(f"[RECEIVED] Sorted chunk from {ip}")

    except Exception as e:
        print(f"[ERROR] Error handling worker {ip}: {e}")
        update_trust_score(ip, success=False)
        log_event(f"Worker {ip} failed: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

def wait_for_workers(server_socket, expected_workers, timeout=60):
    start_time = time.time()
    server_socket.settimeout(10)  # Set a timeout for accept()
    
    while len(CONNECTED_WORKERS) < expected_workers:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"[WARNING] Timeout waiting for workers. Only {len(CONNECTED_WORKERS)} of {expected_workers} connected.")
            break
            
        try:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_worker, args=(conn, addr)).start()
        except socket.timeout:
            print(f"[INFO] Waiting for more workers... ({len(CONNECTED_WORKERS)}/{expected_workers})")
        except Exception as e:
            print(f"[ERROR] Error accepting connection: {e}")
    
    server_socket.settimeout(None)  # Reset timeout

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs(os.path.dirname(SORTED_OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    
    # Check if dataset exists
    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Dataset not found at {DATASET_PATH}")
        exit(1)
        
    data = load_dataset(DATASET_PATH)
    print(f"[INFO] Loaded {len(data)} elements from dataset")
    
    num_workers = int(input("How many workers to connect? "))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(10)  # Increased backlog for more pending connections
        
        print(f"[INFO] Server started on {HOST}:{PORT}")
        print("[INFO] Waiting for workers to connect...")
        
        wait_for_workers(server, num_workers)
        print(f"[INFO] {len(CONNECTED_WORKERS)} workers connected. Dividing chunks...")
        
        # Prepare chunks based on connected workers
        trust_scores = {ip: get_trust_score(ip) for _, ip in CONNECTED_WORKERS}
        chunks = divide_chunks(data, trust_scores)
        
        # ===== Start timing once all workers are connected =====
        sort_start_time = time.time()
        print(f"[TIMING] Starting timing measurement at {time.strftime('%H:%M:%S')}")
        
        # Start a thread for each worker to handle sending and receiving
        threads = []
        for i, (conn, ip) in enumerate(CONNECTED_WORKERS):
            if i < len(chunks):
                _, chunk_data = chunks[i]
                t = threading.Thread(target=worker_task, args=(conn, ip, chunk_data))
                t.start()
                threads.append(t)
            else:
                print(f"[WARNING] No data chunk for worker {ip}")
                conn.close()
        
        # Wait for all worker threads to complete
        for t in threads:
            t.join()
        
        if SORTED_CHUNKS:
            print("[INFO] Merging sorted chunks...")
            final_sorted = list(heapq.merge(*SORTED_CHUNKS))
            print("[INFO] Final merge complete.")
            
            save_sorted_data(final_sorted)
            
            # ===== End timing after everything is complete =====
            sort_end_time = time.time()
            total_sort_time = sort_end_time - sort_start_time
            
            print(f"[SUCCESS] Sorting complete. {len(final_sorted)} elements sorted.")
            print(f"[TIMING] Total sorting time: {total_sort_time:.2f} seconds")
            
            # Save timing information to a file
            with open("data/sort_timing.txt", "w") as f:
                f.write(f"Total elements: {len(final_sorted)}\n")
                f.write(f"Number of workers: {len(CONNECTED_WORKERS)}\n")
                f.write(f"Total sorting time: {total_sort_time:.2f} seconds\n")
                f.write(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sort_start_time))}\n")
                f.write(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sort_end_time))}\n")
            
            print(f"[INFO] Timing information saved to data/sort_timing.txt")
        else:
            print("[WARNING] No data sorted. Check for worker connection issues.")
    
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
    
    finally:
        server.close()
        print("[INFO] Server shut down.")