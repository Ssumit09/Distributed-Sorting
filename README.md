# 🔁 Trust-Aware Distributed Sorting System

A reliable distributed sorting system using a master-worker architecture, where trust scores dynamically influence task distribution to enhance efficiency and scalability.

---

## 🚀 Features

- Distributed architecture with a central master and multiple workers
- Trust score-based dynamic task allocation (range: 1 to 3)
- Merge-based sorting for scalability and parallelism
- Real-time communication using Python sockets
- Execution logging and performance tracking

---

## 🧰 Tech Stack

- Python 3
- `socket` for network communication
- `pickle`, `struct` for data serialization
- JSON for trust score persistence
- Matplotlib (optional) for visualizing performance

---

## 📂 Project Structure

distributed-sorting/
│
├── master.py # Master node: manages task distribution and merging
├── worker.py # Worker node: receives, sorts, and sends back data
├── trust_scores.json # Stores trust scores persistently
├── uniform.txt # Input data file (one integer per line)
├── logs/ # Logs directory
└── results/ # Stores merged sorted output



---

## 🛠️ How to Run

### 1️⃣ Start the Server Node and type how many workers you want to connect
```bash
python server.py
```

### 2️⃣ Start Worker Nodes (Run in separate terminals or systems) must having in same local network
```bash
python worker.py
```


📈 Example Output
Logs each worker’s trust score and task completion

Shows reduction in execution time with increased workers

Outputs a final merged and sorted file in /results/sorted_output.txt


###📌 License
This project is licensed under the MIT License.

###🤝 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

###📬 Contact
For questions or collaboration, feel free to contact [sumeetzhaa09@example.com].
