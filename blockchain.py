import time
import hashlib
import tkinter as tk
from tkinter import messagebox
import json
import os

# --- Wallet ---
class Wallet:
    def __init__(self, name, initial_balance=1000):
        self.name = name
        self.balance = initial_balance
        self.address = hashlib.sha256(name.encode()).hexdigest()

    def can_afford(self, amount):
        return self.balance >= amount

    def deduct(self, amount):
        print(f"[DEBUG] Deducting {amount} from {self.name} (before: {self.balance})")
        if self.can_afford(amount):
            self.balance -= amount
            print(f"[DEBUG] {self.name} new balance: {self.balance}")
            return True
        print(f"[DEBUG] {self.name} cannot afford {amount}")
        return False
        
    def deposit(self, amount):
        self.credit(amount)

    def credit(self, amount):
        self.balance += amount

    def __repr__(self):
        return f"Wallet(name={self.name}, balance={self.balance}, address={self.address[:10]}...)"

# --- Transaction ---
class Transaction:
    def __init__(self, sender_wallet, receiver_wallet, amount):
        self.sender = sender_wallet.address if sender_wallet else "SYSTEM"
        self.receiver = receiver_wallet.address if receiver_wallet else "SYSTEM"
        self.amount = amount
        self.timestamp = time.time()
        self.signature = self.generate_signature()

    def generate_signature(self):
        data = f"{self.sender}{self.receiver}{self.amount}{self.timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    def approve(self, ledger):
        if self.sender == "SYSTEM":
            return True
        sender_wallet = ledger.get_wallet_by_address(self.sender)
        return sender_wallet and sender_wallet.can_afford(self.amount)

    def __repr__(self):
        return (f"Transaction(sender={self.sender[:10]}..., receiver={self.receiver[:10]}..., "
                f"amount={self.amount}, time={self.timestamp:.2f})")

# --- Ledger ---
class Ledger:
    def __init__(self):
        self.wallets = {}
        self.transactions = []

    def add_wallet(self, wallet):
        self.wallets[wallet.address] = wallet

    def get_wallet_by_address(self, address):
        return self.wallets.get(address)

    def record_transaction(self, transaction):
        print(f"[DEBUG] Recording transaction: {transaction}")
        self.transactions.append(transaction)

        if transaction.sender != "SYSTEM":
            sender_wallet = self.get_wallet_by_address(transaction.sender)
            print(f"[DEBUG] Sender wallet: {sender_wallet}")
            if sender_wallet:
                sender_wallet.deduct(transaction.amount)

        if transaction.receiver != "SYSTEM":
            receiver_wallet = self.get_wallet_by_address(transaction.receiver)
            print(f"[DEBUG] Receiver wallet: {receiver_wallet}")
            if receiver_wallet:
                receiver_wallet.deposit(transaction.amount)

    def __repr__(self):
        return "\n".join(str(wallet) for wallet in self.wallets.values())

# --- Block ---
class Block:
    def __init__(self, transactions, previous_hash):
        self.transactions = transactions
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        tx_data = "".join(tx.signature for tx in self.transactions)
        block_data = f"{tx_data}{self.timestamp}{self.previous_hash}"
        return hashlib.sha256(block_data.encode()).hexdigest()

    def __repr__(self):
        return (f"Block(hash={self.hash[:10]}..., prev={self.previous_hash[:10]}..., "
                f"tx_count={len(self.transactions)}, time={self.timestamp:.2f})")

# --- Blockchain ---
class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_block(self):
        previous_hash = self.chain[-1].hash if self.chain else "GENESIS"
        block = Block(self.pending_transactions, previous_hash)
        self.chain.append(block)
        self.pending_transactions = []
        return block

    def __repr__(self):
        return "\n".join(str(block) for block in self.chain)

# --- GUI Class ---
class BlockchainGUI:
    def __init__(self, master):
        self.master = master
        master.title("Blockchain Simulation")

        # --- Top Section: Controls ---
        self.top_frame = tk.Frame(master)
        self.top_frame.pack(pady=10)

        # Wallet creation row
        wallet_row_frame = tk.Frame(self.top_frame)
        wallet_row_frame.pack(fill=tk.X)

        tk.Label(wallet_row_frame, text="Wallet\n Name").pack(side=tk.LEFT, padx=5)
        self.wallet_name_entry = tk.Entry(wallet_row_frame, width=10)
        self.wallet_name_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(wallet_row_frame, text="Amount").pack(side=tk.LEFT, padx=5)
        self.initial_amount_entry = tk.Entry(wallet_row_frame, width=10)
        self.initial_amount_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(wallet_row_frame, text="Create Wallet", command=self.create_wallet).pack(side=tk.LEFT, padx=10)
        tk.Button(wallet_row_frame, text="Adjust Balance", command=self.adjust_balance).pack(side=tk.LEFT, padx=5)

        tk.Button(wallet_row_frame, text="All Wallets", command=self.show_wallets).pack(side=tk.RIGHT, padx=10)

        # Transaction row
        transaction_row_frame = tk.Frame(self.top_frame)
        transaction_row_frame.pack(fill=tk.X)

        tk.Label(transaction_row_frame, text="Sender").pack(side=tk.LEFT, padx=5)
        self.sender_entry = tk.Entry(transaction_row_frame, width=10)
        self.sender_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(transaction_row_frame, text="Receiver").pack(side=tk.LEFT, padx=5)
        self.receiver_entry = tk.Entry(transaction_row_frame, width=10)
        self.receiver_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(transaction_row_frame, text="Amount").pack(side=tk.LEFT, padx=5)
        self.amount_entry = tk.Entry(transaction_row_frame, width=10)
        self.amount_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(transaction_row_frame, text="Add Transaction", command=self.add_transaction).pack(side=tk.LEFT, padx=10)
        tk.Button(transaction_row_frame, text="All Transactions", command=self.show_transactions).pack(side=tk.RIGHT, padx=10)

        # --- Middle Section: Messages ---
        self.middle_frame = tk.Frame(master)
        self.middle_frame.pack(pady=10)
        self.message_label = tk.Label(self.middle_frame, text="", fg="blue", justify="left", anchor="w")
        self.message_label.pack()

        # --- Bottom Section: Blockchain Canvas with Scrollable Frame ---
        self.bottom_frame = tk.Frame(master)
        self.bottom_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.bottom_frame, height=220, bg="white")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<MouseWheel>", self.zoom_canvas)  # Windows
        self.canvas.bind("<Button-4>", self.zoom_canvas)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom_canvas)    # Linux scroll down

        # Right-click menu
        self.canvas.bind("<Button-3>", self.show_canvas_menu)
        self.create_canvas_menu()

        # --- Blockchain Data ---
        self.ledger = Ledger()
        self.chain = Blockchain()
        self.wallets_by_name = {}
        self.system_wallet = Wallet("SYSTEM", initial_balance=0)
        
        self.zoom_scale = 1.0

    def create_wallet(self):
        name = self.wallet_name_entry.get()
        amount = self.initial_amount_entry.get()
        if not name:
            self.message_label.config(text="Wallet name is required.")
            return
        try:
            initial = int(amount) if amount else 0
            wallet = Wallet(name, initial_balance=initial)
            self.ledger.add_wallet(wallet)
            self.wallets_by_name[name] = wallet
            self.message_label.config(text=f"Wallet '{name}' created with {initial} units.")
        except ValueError:
            self.message_label.config(text="Invalid amount.")

    def adjust_balance(self):
        name = self.wallet_name_entry.get()
        try:
            amount = int(self.initial_amount_entry.get())
            wallet = self.wallets_by_name.get(name)
            if wallet:
                if amount == 0:
                    self.message_label.config(text="Amount must be non-zero.")
                    return

                # Create SYSTEM transaction
                if amount > 0:
                    tx = Transaction(None, wallet, amount)  # SYSTEM deposit
                else:
                    if wallet.can_afford(-amount):
                        tx = Transaction(wallet, self.system_wallet, abs(amount))  # SYSTEM withdrawal
                    else:
                        self.message_label.config(text=f"{name} cannot withdraw {-amount}: insufficient funds.")
                        return

                if tx.approve(self.ledger):
                    self.ledger.record_transaction(tx)  # ← This updates balances

                    self.chain.add_transaction(tx)
                    self.chain.mine_block()
                    self.message_label.config(text=f"{name} balance adjusted by {amount}. New balance: {wallet.balance}")
                    self.draw_chain()
                else:
                    self.message_label.config(text=f"Transaction failed: {name} cannot afford {tx.amount}.")
            else:
                self.message_label.config(text="Wallet not found.")
        except ValueError:
            self.message_label.config(text="Invalid amount.")
        
    def add_transaction(self):
        sender_name = self.sender_entry.get()
        receiver_name = self.receiver_entry.get()
        try:
            amount = int(self.amount_entry.get())
            sender = self.wallets_by_name.get(sender_name)
            receiver = self.wallets_by_name.get(receiver_name)
            if sender and receiver:
                tx = Transaction(sender, receiver, amount)
                print(f"DEBUG: sender={sender.name}, address={sender.address}")
                print(f"DEBUG: receiver={receiver.name}, address={receiver.address}")
                print(f"DEBUG: tx.sender={tx.sender}, tx.receiver={tx.receiver}")
                if tx.approve(self.ledger):
                    self.ledger.record_transaction(tx)
                    self.chain.add_transaction(tx)
                    self.chain.mine_block()
                    sender_balance = sender.balance
                    receiver_balance = receiver.balance
                    self.message_label.config(
                        text=f"Transaction: {sender_name} → {receiver_name} ({amount})\n"
                             f"{sender_name} balance: {sender_balance}\n"
                             f"{receiver_name} balance: {receiver_balance}"
                    )
                    self.draw_chain()
                else:
                    self.message_label.config(text="Transaction failed: insufficient funds.")
            else:
                self.message_label.config(text="Sender or receiver not found.")
        except ValueError:
            self.message_label.config(text="Invalid transaction amount.")

    def zoom_canvas(self, event):
        # Determine zoom direction
        if event.delta > 0 or event.num == 4:
            self.zoom_scale *= 1.1
        elif event.delta < 0 or event.num == 5:
            self.zoom_scale /= 1.1

        self.draw_chain()
    
    def draw_chain(self):
        self.canvas.delete("all")
        x, y = 20, 20
        block_width = int(150 * self.zoom_scale)
        block_height = int(50 * self.zoom_scale)
        spacing = int(20 * self.zoom_scale)
        font_size = max(6, int(9 * self.zoom_scale))

        for i, block in enumerate(self.chain.chain):
            self.canvas.create_rectangle(x, y, x + block_width, y + block_height, fill="lightblue", outline="black")
            self.canvas.create_text(x + 10, y + 10, anchor="nw", text=f"Block {i}", font=("Arial", font_size, "bold"))

            tx_y = y + 30
            for tx in block.transactions:
                sender = tx.sender[:6] if tx.sender != "SYSTEM" else "SYSTEM"
                receiver = tx.receiver[:6] if tx.receiver != "SYSTEM" else "SYSTEM"
                tx_text = f"{sender} → {receiver}: {tx.amount}"
                color = "darkorange" if "SYSTEM" in (tx.sender, tx.receiver) else "black"
                self.canvas.create_text(x + 10, tx_y, anchor="nw", text=tx_text, fill=color, font=("Arial", font_size))
                tx_y += int(15 * self.zoom_scale)

            if i < len(self.chain.chain) - 1:
                x_center = x + block_width
                next_x = x + block_width + spacing
                self.canvas.create_line(x_center, y + block_height // 2, next_x, y + block_height // 2, arrow=tk.LAST)

            x += block_width + spacing

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.xview_moveto(1.0) 
                
    def show_wallets(self):
        lines = []
        for wallet in self.wallets_by_name.values():
            lines.append(f"{wallet.name}: {wallet.balance} units")
        self.message_label.config(text="All Wallets:\n" + "\n".join(lines))

    def show_transactions(self):
        lines = []
        for tx in self.ledger.transactions:
            sender = tx.sender[:6] if tx.sender != "SYSTEM" else "SYSTEM"
            receiver = tx.receiver[:6]
            lines.append(f"{sender} → {receiver}: {tx.amount}")
        self.message_label.config(text="All Transactions:\n" + "\n".join(lines))

    def save_state(self):
        data = {
            "wallets": [
                {"name": w.name, "balance": w.balance, "address": w.address}
                for w in self.wallets_by_name.values()
            ],
            "transactions": [
                {
                    "sender": tx.sender,
                    "receiver": tx.receiver,
                    "amount": tx.amount,
                    "timestamp": tx.timestamp,
                    "signature": tx.signature
                }
                for tx in self.ledger.transactions
            ]
        }
        with open("blockchain_state.json", "w") as f:
            json.dump(data, f, indent=2)
        self.message_label.config(text="State saved to blockchain_state.json")

    def load_state(self):
        if not os.path.exists("blockchain_state.json"):
            self.message_label.config(text="No saved file found.")
            return

        with open("blockchain_state.json", "r") as f:
            data = json.load(f)

        # Reset state
        self.ledger = Ledger()
        self.chain = Blockchain()
        self.wallets_by_name = {}

        # Rebuild wallets
        for w in data["wallets"]:
            wallet = Wallet(w["name"], initial_balance=0)
            wallet.balance = w["balance"]
            wallet.address = w["address"]
            self.ledger.add_wallet(wallet)
            self.wallets_by_name[w["name"]] = wallet

        # Rebuild transactions and mine them into blocks
        for tx_data in data["transactions"]:
            sender_wallet = None
            receiver_wallet = None

            # Match sender wallet by address (unless it's SYSTEM)
            if tx_data["sender"] != "SYSTEM":
                sender_wallet = next(
                    (w for w in self.wallets_by_name.values() if w.address == tx_data["sender"]),
                    None
                )

            # Match receiver wallet by address (unless it's SYSTEM)
            if tx_data["receiver"] != "SYSTEM":
                receiver_wallet = next(
                    (w for w in self.wallets_by_name.values() if w.address == tx_data["receiver"]),
                    None
                )

            # Skip if both sender and receiver are None (invalid transaction)
            if sender_wallet is None and receiver_wallet is None:
                continue

            tx = Transaction(sender_wallet, receiver_wallet, tx_data["amount"])
            tx.timestamp = tx_data["timestamp"]
            tx.signature = tx_data["signature"]
            self.ledger.record_transaction(tx)
            self.chain.add_transaction(tx)
            self.chain.mine_block()

        self.message_label.config(text="State loaded from blockchain_state.json")
        self.draw_chain()
        
    def create_canvas_menu(self):
        self.canvas_menu = tk.Menu(self.master, tearoff=0)
        self.canvas_menu.add_command(label="Save", command=self.save_state)
        self.canvas_menu.add_command(label="Load", command=self.load_state)
        
    def show_canvas_menu(self, event):
        try:
            self.canvas_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.canvas_menu.grab_release()

# --- Launch GUI ---
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("860x400")  # Fixed window size
    root.resizable(False, False)

    app = BlockchainGUI(root)
    root.mainloop()
