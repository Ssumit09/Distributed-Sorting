
import socket
import pickle
import struct
import time
import os
import datetime

# Implementing merge sort function in case the utils module is missing
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def recv_all(sock, length):
    data = b''
    while len(data) < length:
        try:
            more = sock.recv(length - len(data))
            if not more:
                raise EOFError('Socket closed before receiving full data')
            data += more
        except socket.timeout:
            print("[WARNING] Socket timeout while receiving data. Retrying...")
            continue
    return data

def save_chunk(chunk, is_sorted=False):
    # Create directory if it doesn't exist
    os.makedirs("worker_chunks", exist_ok=True)
    
    # Generate timestamp for unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use hostname as part of filename if available
    try:
        import socket
        hostname = socket.gethostname()
    except:
        hostname = "worker"
    
    # Create filename
    prefix = "sorted" if is_sorted else "received"
    filename = f"worker_chunks/{prefix}_chunk_{hostname}_{timestamp}.txt"
    
    # Save chunk to file
    with open(filename, "w") as f:
        for num in chunk:
            f.write(f"{num}\n")
    
    return filename

def main():
    # Allow configuring server address via environment variables or input
    server_host = os.environ.get("SERVER_HOST", "")
    if not server_host:
        server_host = input("Enter server IP address: ") or "172.29.23.30"
        
    server_port = int(os.environ.get("SERVER_PORT", "5000"))
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"[INFO] Connecting to server at {server_host}:{server_port}...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(15)  # Set timeout for operations
                sock.connect((server_host, server_port))
                print("[INFO] Connected to server.")
                
                # Receive chunk
                raw_msglen = recv_all(sock, 4)
                msglen = struct.unpack('>I', raw_msglen)[0]
                
                print(f"[INFO] Receiving data chunk of size {msglen} bytes...")
                data = recv_all(sock, msglen)
                chunk = pickle.loads(data)
                print(f"[INFO] Received chunk from server of size {len(chunk)}.")
                
                # Save received chunk to file as proof
                received_file = save_chunk(chunk, is_sorted=False)
                print(f"[INFO] Saved received chunk to {received_file}")
                
                # Sort chunk using merge sort
                print("[INFO] Sorting data...")
                start_time = time.time()
                sorted_chunk = merge_sort(chunk)
                elapsed = time.time() - start_time
                print(f"[INFO] Sorted chunk in {elapsed:.2f} seconds. Sending back to server.")
                
                # Save sorted chunk to file as proof
                sorted_file = save_chunk(sorted_chunk, is_sorted=True)
                print(f"[INFO] Saved sorted chunk to {sorted_file}")
                
                # Send sorted chunk back
                sorted_data = pickle.dumps(sorted_chunk)
                print(f"[INFO] Sending {len(sorted_data)} bytes back to server...")
                sock.sendall(struct.pack('>I', len(sorted_data)))
                sock.sendall(sorted_data)
                print("[INFO] Sent sorted chunk to server.")
                
                # Wait for acknowledgement or just return
                time.sleep(1)
                
                print(f"[SUCCESS] Worker completed task. Proof files saved at:")
                print(f"  - Received chunk: {received_file}")
                print(f"  - Sorted chunk: {sorted_file}")
                break  # Success, exit the retry loop
                
        except ConnectionRefusedError:
            retry_count += 1
            wait_time = 5 * retry_count
            print(f"[ERROR] Connection refused. Retrying in {wait_time} seconds... ({retry_count}/{max_retries})")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"[ERROR] Connection/sorting failed: {e}")
            retry_count += 1
            if retry_count < max_retries:
                print(f"[INFO] Retrying in 5 seconds... ({retry_count}/{max_retries})")
                time.sleep(5)
            else:
                print("[ERROR] Maximum retries reached. Exiting.")
                break

if __name__ == "__main__":
    main()