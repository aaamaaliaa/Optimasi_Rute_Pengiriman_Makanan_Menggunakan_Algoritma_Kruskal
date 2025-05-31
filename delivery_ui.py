import tkinter as tk
from tkinter import ttk, messagebox
from tkinterweb.htmlwidgets import HtmlFrame
from delivery_controller import DeliveryController
import os
import logging
import webbrowser
from PIL import Image, ImageTk

logging.basicConfig(level=logging.DEBUG, filename="delivery.log", filemode="w",
                    format="%(asctime)s - %(levelname)s - %(message)s")

class DeliveryUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rute Pengiriman Makanan - Cirebon")
        self.root.geometry("1200x900")
        self.controller = DeliveryController()
        self.editing_order_id = None
        self.progress_counter = 0
        self.progress_max = 0
        
        # Load icons
        icon_names = ["depot", "order", "route", "export", "back", "start", "map"]
        self.icons = {}
        icon_folder = os.path.join(os.getcwd(), "icon")
        if not os.path.exists(icon_folder):
            os.makedirs(icon_folder)
            logging.warning(f"Folder {icon_folder} dibuat.")
        
        available_icons = [f[:-4] for f in os.listdir(icon_folder) if f.endswith(".png")]
        for icon_name in icon_names:
            icon_path = os.path.join(icon_folder, f"{icon_name}.png")
            if icon_name in available_icons and os.path.exists(icon_path):
                try:
                    icon = tk.PhotoImage(file=icon_path).subsample(2, 2)
                    self.icons[icon_name] = icon
                    logging.info(f"Ikon {icon_name}.png dimuat.")
                except Exception as e:
                    logging.error(f"Gagal memuat ikon {icon_name}.png: {str(e)}")
                    self.icons[icon_name] = None
            else:
                logging.warning(f"Ikon {icon_name}.png tidak ditemukan.")
                self.icons[icon_name] = None

        # Setup background
        self.setup_background()

        self.setup_styles()
        
        self.container = ttk.Frame(self.root)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=0)
        self.root.rowconfigure(0, weight=0)
        
        self.pages = {
            "main": ttk.Frame(self.container, style="Main.TFrame"),
            "depot": ttk.Frame(self.container, style="Depot.TFrame"),
            "order": ttk.Frame(self.container, style="Order.TFrame")
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")
        
        self.setup_main_page()
        self.setup_depot_page()
        self.setup_order_page()
        self.show_page("main")

    def setup_background(self):
        self.root.configure(bg="#E8F5E9") 

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TFrame", background="#E8F5E9")  
        style.configure("Depot.TFrame", background="#E3F2FD") 
        style.configure("Order.TFrame", background="#FFFDE7")  
        style.configure("Header.TFrame", background="#4CAF50")  
        style.configure("Inner.TFrame", background="#FFFFFF", borderwidth=1, relief="solid", bordercolor="#E0E0E0")
        style.configure("TLabelframe", background="#FFFFFF", relief="flat")
        style.configure("TLabelframe.Label", background="#FFFFFF", foreground="#333333", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", background="#4CAF50", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=10)
        style.map("TButton", background=[("active", "#81C784")])
        style.configure("Icon.TButton", background="#FFFFFF", foreground="#333333", font=("Segoe UI", 9), padding=10)
        style.map("Icon.TButton", background=[("active", "#E8ECEF")])
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#333333", font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#4CAF50", foreground="#FFFFFF", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#81C784")])
        style.configure("TLabel", background="#FFFFFF", foreground="#333333", font=("Segoe UI", 9))
        style.configure("TProgressbar", troughcolor="#E0E0E0", background="#4CAF50")

    def show_page(self, page_name):
        self.pages[page_name].tkraise()

    def setup_main_page(self):
        main_frame = ttk.Frame(self.pages["main"], style="Main.TFrame", padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.pages["main"].columnconfigure(0, weight=1)
        self.pages["main"].rowconfigure(0, weight=1)
        
        header_frame = ttk.Frame(main_frame, style="Header.TFrame")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_label = ttk.Label(
            header_frame,
            text="Rute Pengiriman Makanan - Cirebon",
            font=("Segoe UI", 24, "bold"),
            background="#4CAF50",
            foreground="#FFFFFF"
        )
        header_label.grid(row=0, column=0, pady=20, padx=20)
        
        welcome_label = ttk.Label(
            main_frame,
            text="Selamat datang! Atur dapur, tambah pesanan, dan hitung rute pengiriman dengan mudah.",
            font=("Segoe UI", 12, "italic"),
            background="#E8F5E9",
            foreground="#333333"
        )
        welcome_label.grid(row=1, column=0, pady=10)
        
        start_button = ttk.Button(
            main_frame,
            text="Mulai Mengatur Pengiriman" if not self.icons["start"] else "Mulai Mengatur Pengiriman",
            image=self.icons["start"],
            compound="right",
            command=lambda: self.show_page("depot")
        )
        start_button.grid(row=2, column=0, pady=20)
        
        buttons_frame = ttk.Frame(main_frame, style="Inner.TFrame", padding="20")
        buttons_frame.grid(row=3, column=0, pady=20)
        
        depot_button = ttk.Button(
            buttons_frame,
            text="Atur Dapur" if not self.icons["depot"] else "Atur Dapur",
            image=self.icons["depot"],
            compound="top",
            style="Icon.TButton",
            command=lambda: self.show_page("depot")
        )
        depot_button.grid(row=0, column=0, padx=20, pady=10)
        
        order_button = ttk.Button(
            buttons_frame,
            text="Tambah Pesanan" if not self.icons["order"] else "Tambah Pesanan",
            image=self.icons["order"],
            compound="top",
            style="Icon.TButton",
            command=self.check_depot_and_navigate
        )
        order_button.grid(row=0, column=1, padx=20, pady=10)
        
        route_button = ttk.Button(
            buttons_frame,
            text="Hitung Rute" if not self.icons["route"] else "Hitung Rute",
            image=self.icons["route"],
            compound="top",
            style="Icon.TButton",
            command=self.check_depot_and_navigate
        )
        route_button.grid(row=1, column=0, padx=20, pady=10)
        
        export_button = ttk.Button(
            buttons_frame,
            text="Ekspor ke CSV" if not self.icons["export"] else "Ekspor ke CSV",
            image=self.icons["export"],
            compound="top",
            style="Icon.TButton",
            command=self.check_depot_and_navigate
        )
        export_button.grid(row=1, column=1, padx=20, pady=10)
        
        map_button = ttk.Button(
            buttons_frame,
            text="Lihat Semua Lokasi" if not self.icons["map"] else "Lihat Semua Lokasi",
            image=self.icons["map"],
            compound="top",
            style="Icon.TButton",
            command=self.display_all_points_map
        )
        map_button.grid(row=1, column=2, padx=20, pady=10)

    def check_depot_and_navigate(self):
        if not self.controller.depot:
            messagebox.showerror("Error", "Harap tetapkan dapur terlebih dahulu di menu Atur Dapur.")
        else:
            self.show_page("order")

    def setup_depot_page(self):
        depot_frame = ttk.LabelFrame(self.pages["depot"], text="Atur Dapur/Restoran", padding="9", style="TLabelframe")
        depot_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        
        ttk.Label(
            depot_frame,
            text="Masukkan nama dan alamat dapur (restoran) tempat makanan diambil.",
            font=("Segoe UI", 9, "italic"),
            background="#E3F2FD"
        ).grid(row=0, column=0, columnspan=6, pady=5)
        
        ttk.Label(depot_frame, text="Nama Dapur:", background="#E3F2FD").grid(row=1, column=0, padx=5)
        self.depot_name_entry = ttk.Entry(depot_frame, font=("Segoe UI", 9))
        self.depot_name_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(depot_frame, text="Alamat Dapur:", background="#E3F2FD").grid(row=1, column=2, padx=5)
        self.depot_address_entry = ttk.Entry(depot_frame, font=("Segoe UI", 9))
        self.depot_address_entry.grid(row=1, column=3, columnspan=2, padx=5, sticky="ew")
        
        self.depot_progress = ttk.Progressbar(depot_frame, orient="horizontal", mode="determinate")
        self.depot_progress.grid(row=2, column=0, columnspan=5, padx=5, pady=5, sticky="ew")
        
        depot_button = ttk.Button(
            depot_frame,
            text="Simpan Dapur" if not self.icons["depot"] else "Simpan Dapur",
            image=self.icons["depot"],
            compound="left",
            command=self.set_depot
        )
        depot_button.grid(row=1, column=5, padx=5)
        
        back_button = ttk.Button(
            depot_frame,
            text="Kembali" if not self.icons["back"] else "Kembali",
            image=self.icons["back"],
            compound="left",
            command=lambda: self.show_page("main")
        )
        back_button.grid(row=3, column=0, padx=5, pady=10)

    def setup_order_page(self):
        main_frame = ttk.Frame(self.pages["order"], style="Order.TFrame", padding="5")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.pages["order"].columnconfigure(0, weight=1)
        self.pages["order"].rowconfigure(4, weight=1)
        
        back_button = ttk.Button(
            main_frame,
            text="Kembali ke Menu" if not self.icons["back"] else "Kembali ke Menu",
            image=self.icons["back"],
            compound="left",
            command=lambda: self.show_page("main")
        )
        back_button.grid(row=0, column=0, sticky="nw", padx=5, pady=2)
        
        order_frame = ttk.LabelFrame(main_frame, text="Tambah/Edit Pesanan", padding="5", style="TLabelframe")
        order_frame.grid(row=1, column=0, sticky="ew", pady=2, padx=5)
        order_frame.columnconfigure(1, weight=1)
        order_frame.columnconfigure(3, weight=1)
        order_frame.columnconfigure(5, weight=1)
        
        ttk.Label(
            order_frame,
            text="Masukkan detail pesanan: nama kurir, pelanggan, alamat, dan pesanan. Tujuan adalah alamat pengiriman (bisa sama atau berbeda dengan alamat pelanggan).",
            font=("Segoe UI", 9, "italic")
        ).grid(row=0, column=0, columnspan=6, pady=2, sticky="ew")
        
        ttk.Label(order_frame, text="Nama Kurir:").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        self.courier_entry = ttk.Entry(order_frame, font=("Segoe UI", 9))
        self.courier_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(order_frame, text="Nama Pelanggan:").grid(row=1, column=2, padx=5, pady=2, sticky="e")
        self.customer_entry = ttk.Entry(order_frame, font=("Segoe UI", 9))
        self.customer_entry.grid(row=1, column=3, padx=5, pady=2, sticky="ew")
        
        ttk.Label(order_frame, text="Alamat Pelanggan:").grid(row=1, column=4, padx=5, pady=2, sticky="e")
        self.customer_address_entry = ttk.Entry(order_frame, font=("Segoe UI", 9))
        self.customer_address_entry.grid(row=1, column=5, padx=5, pady=2, sticky="ew")
        
        ttk.Label(order_frame, text="Tujuan Pengiriman:").grid(row=2, column=0, padx=5, pady=2, sticky="e")
        self.destination_entry = ttk.Entry(order_frame, font=("Segoe UI", 9))
        self.destination_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(order_frame, text="Alamat Pengiriman:").grid(row=2, column=2, padx=5, pady=2, sticky="e")
        self.destination_address_entry = ttk.Entry(order_frame, font=("Segoe UI", 9))
        self.destination_address_entry.grid(row=2, column=3, padx=5, pady=2, sticky="ew")
        
        ttk.Label(order_frame, text="Pesanan Makanan:").grid(row=2, column=4, padx=5, pady=2, sticky="e")
        self.order_entry = ttk.Entry(order_frame, font=("Segoe UI", 9))
        self.order_entry.grid(row=2, column=5, padx=5, pady=2, sticky="ew")
        
        ttk.Label(order_frame, text="Harga (Rp):").grid(row=3, column=0, padx=5, pady=2, sticky="e")
        self.price_entry = ttk.Entry(order_frame, font=("Segoe UI", 9))
        self.price_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        
        self.order_progress = ttk.Progressbar(order_frame, orient="horizontal", mode="determinate")
        self.order_progress.grid(row=4, column=0, columnspan=6, padx=5, pady=2, sticky="ew")
        
        save_button = ttk.Button(
            order_frame,
            text="Simpan Pesanan" if not self.icons["order"] else "Simpan Pesanan",
            image=self.icons["order"],
            compound="left",
            command=self.save_order
        )
        save_button.grid(row=3, column=5, padx=5, pady=2, sticky="e")
        
        button_frame = ttk.Frame(main_frame, style="Inner.TFrame")
        button_frame.grid(row=2, column=0, pady=2, padx=5)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        
        route_button = ttk.Button(
            button_frame,
            text="Hitung Semua Rute" if not self.icons["route"] else "Hitung Semua Rute",
            image=self.icons["route"],
            compound="left",
            command=self.display_routes
        )
        route_button.grid(row=0, column=0, padx=5, pady=2, sticky="e")
        
        multi_drop_button = ttk.Button(
            button_frame,
            text="Hitung Rute Gabungan" if not self.icons["route"] else "Hitung Rute Gabungan",
            image=self.icons["route"],
            compound="left",
            command=self.display_multi_drop_route
        )
        multi_drop_button.grid(row=0, column=1, padx=5, pady=2)
        
        export_button = ttk.Button(
            button_frame,
            text="Ekspor ke CSV" if not self.icons["export"] else "Ekspor ke CSV",
            image=self.icons["export"],
            compound="left",
            command=self.export_to_csv
        )
        export_button.grid(row=0, column=2, padx=5, pady=2, sticky="w")
        
        self.tree = ttk.Treeview(
            main_frame,
            columns=("ID", "Kurir", "Pelanggan", "Tujuan", "Pesanan", "Harga", "Jarak", "Waktu", "Peta"),
            show="headings"
        )
        self.tree.heading("ID", text="ID Pesanan")
        self.tree.heading("Kurir", text="Kurir")
        self.tree.heading("Pelanggan", text="Pelanggan")
        self.tree.heading("Tujuan", text="Tujuan Pengiriman")
        self.tree.heading("Pesanan", text="Pesanan")
        self.tree.heading("Harga", text="Harga (Rp)")
        self.tree.heading("Jarak", text="Jarak (km)")
        self.tree.heading("Waktu", text="Waktu (menit)")
        self.tree.heading("Peta", text="Peta")
        self.tree.column("ID", width=100)
        self.tree.column("Kurir", width=100)
        self.tree.column("Pelanggan", width=100)
        self.tree.column("Tujuan", width=100)
        self.tree.column("Pesanan", width=150)
        self.tree.column("Harga", width=100)
        self.tree.column("Jarak", width=100)
        self.tree.column("Waktu", width=100)
        self.tree.column("Peta", width=100)
        self.tree.grid(row=3, column=0, sticky="nsew", padx=5, pady=2)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        
        self.tree.tag_configure("evenrow", background="#F5F5F5")
        self.tree.tag_configure("oddrow", background="#FFFFFF")
        
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=3, column=1, sticky="ns", pady=2)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.map_frame = HtmlFrame(main_frame, messages_enabled=False)
        self.map_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=2)
        main_frame.rowconfigure(4, weight=1)
        self.map_frame.load_html("<p style='color:#333333;font-family:Segoe UI;'>Klik dua kali pada baris pesanan untuk melihat peta rute.</p>")
        
        self.total_label = ttk.Label(
            main_frame,
            text="Total: Jarak = 0 km, Waktu = 0 menit, Harga = Rp 0",
            background="#FFFDE7",
            foreground="#333333",
            font=("Segoe UI", 9)
        )
        self.total_label.grid(row=5, column=0, pady=2, sticky="ew")
        
        self.status_label = ttk.Label(
            main_frame,
            text="Masukkan pesanan baru atau edit pesanan yang ada.",
            background="#FFFDE7",
            foreground="#333333",
            font=("Segoe UI", 9)
        )
        self.status_label.grid(row=6, column=0, pady=2, sticky="ew")

    def update_progress(self):
        self.progress_counter += 1
        progress = (self.progress_counter / self.progress_max) * 100
        self.depot_progress["value"] = progress
        self.order_progress["value"] = progress
        self.root.update()

    def set_depot(self):
        name = self.depot_name_entry.get()
        address = self.depot_address_entry.get()
        self.progress_counter = 0
        self.progress_max = 1
        self.depot_progress["maximum"] = 100
        self.depot_progress["value"] = 0
        
        success, message = self.controller.set_depot(name, address, self.update_progress)
        messagebox.showinfo("Sukses", message) if success else messagebox.showerror("Error", message)
        self.status_label.config(text=message)
        if success:
            self.depot_name_entry.delete(0, tk.END)
            self.depot_address_entry.delete(0, tk.END)
            self.show_page("order")
        self.depot_progress["value"] = 0

    def save_order(self):
        courier = self.courier_entry.get()
        customer = self.customer_entry.get()
        customer_address = self.customer_address_entry.get()
        destination = self.destination_entry.get()
        destination_address = self.destination_address_entry.get()
        order = self.order_entry.get()
        price = self.price_entry.get()
        
        if not all([courier, customer, customer_address, destination, destination_address, order, price]):
            messagebox.showerror("Error", "Semua kolom harus diisi.")
            self.status_label.config(text="Semua kolom harus diisi.")
            return
        
        self.progress_counter = 0
        self.progress_max = 2
        self.order_progress["maximum"] = 100
        self.order_progress["value"] = 0
        
        success, message = self.controller.add_or_update_order(
            self.editing_order_id, courier, customer, customer_address, destination, destination_address, order, price, self.update_progress
        )
        messagebox.showinfo("Sukses", message) if success else messagebox.showerror("Error", message)
        self.status_label.config(text=message)
        if success:
            self.clear_order_form()
            self.editing_order_id = None
        self.order_progress["value"] = 0

    def clear_order_form(self):
        self.courier_entry.delete(0, tk.END)
        self.customer_entry.delete(0, tk.END)
        self.customer_address_entry.delete(0, tk.END)
        self.destination_entry.delete(0, tk.END)
        self.destination_address_entry.delete(0, tk.END)
        self.order_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)

    def display_routes(self):
        self.tree.delete(*self.tree.get_children())
        self.map_frame.load_html("<p style='color:#333333;font-family:Segoe UI;'>Klik dua kali pada baris pesanan untuk melihat peta rute.</p>")
        total_distance = 0
        total_time = 0
        total_price = 0
        
        for i, order in enumerate(self.controller.orders):
            points, route, results, error = self.controller.calculate_route_for_order(order)
            if error:
                messagebox.showerror("Error", f"Pesanan {order['id'][:8]}: {error}")
                self.status_label.config(text=f"Error pada pesanan {order['id'][:8]}: {error}")
                continue
            
            total_distance_order, segment_distances, segment_times = results
            map_filename = self.controller.generate_map_for_order(order, points, route, segment_distances, segment_times)
            
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                order["id"][:8],
                order["courier"],
                order["customer"],
                order["destination"],
                order["order"],
                f"{order['price']:,.0f}",
                f"{total_distance_order:.2f}",
                f"{sum(segment_times):.2f}",
                map_filename
            ), tags=(tag,))
            
            total_distance += total_distance_order
            total_time += sum(segment_times)
            total_price += order["price"]
        
        points, route, results, mst_edges, error = self.controller.calculate_multi_drop_route()
        if not error:
            total_distance_multi, segment_distances, segment_times = results
            map_filename = self.controller.generate_map_for_multi_drop(points, route, segment_distances, segment_times, mst_edges)
            self.tree.insert("", "end", values=(
                "Multi-Drop",
                self.controller.orders[0]["courier"] if self.controller.orders else "N/A",
                "Semua",
                "Semua",
                "; ".join(o["order"] for o in self.controller.orders),
                f"{total_price:,.0f}",
                f"{total_distance_multi:.2f}",
                f"{sum(segment_times):.2f}",
                map_filename
            ), tags=("oddrow",))
        
        self.total_label.config(text=f"Total: Jarak = {total_distance:.2f} km, Waktu = {total_time:.2f} menit, Harga = Rp {total_price:,.0f}")
        self.status_label.config(text="Rute berhasil dihitung." if self.controller.orders else "Tidak ada pesanan.")

    def display_multi_drop_route(self):
        self.tree.delete(*self.tree.get_children())
        self.map_frame.load_html("<p style='color:#333333;font-family:Segoe UI;'>Klik dua kali pada baris untuk melihat peta rute gabungan.</p>")
        
        points, route, results, mst_edges, error = self.controller.calculate_multi_drop_route()
        if error:
            messagebox.showerror("Error", error)
            self.status_label.config(text=error)
            return
        
        total_distance, segment_distances, segment_times = results
        map_filename = self.controller.generate_map_for_multi_drop(points, route, segment_distances, segment_times, mst_edges)
        
        total_price = sum(order["price"] for order in self.controller.orders)
        self.tree.insert("", "end", values=(
            "Multi-Drop",
            self.controller.orders[0]["courier"] if self.controller.orders else "N/A",
            "Semua",
            "Semua",
            "; ".join(o["order"] for o in self.controller.orders),
            f"{total_price:,.0f}",
            f"{total_distance:.2f}",
            f"{sum(segment_times):.2f}",
            map_filename
        ), tags=("oddrow",))
        
        self.status_label.config(text="Rute gabungan berhasil dihitung.")

    def display_all_points_map(self):
        filename, error = self.controller.generate_all_points_map()
        if error:
            messagebox.showerror("Error", error)
            self.status_label.config(text=error)
            return
        
        try:
            self.map_frame.load_file(filename)
            logging.info(f"Peta semua lokasi dimuat: {filename}")
            self.status_label.config(text=f"Menampilkan peta semua lokasi: {filename}")
        except Exception as e:
            logging.error(f"Gagal memuat peta di aplikasi: {str(e)}")
            webbrowser.open(filename)
            self.status_label.config(text=f"Peta semua lokasi dibuka di browser: {filename}")

    def on_tree_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        order_id = item["values"][0]
        
        for order in self.controller.orders:
            if order["id"][:8] == order_id:
                self.clear_order_form()
                self.courier_entry.insert(0, order["courier"])
                self.customer_entry.insert(0, order["customer"])
                self.customer_address_entry.insert(0, order["customer_address"])
                self.destination_entry.insert(0, order["destination"])
                self.destination_address_entry.insert(0, order["destination_address"])
                self.order_entry.insert(0, order["order"])
                self.price_entry.insert(0, str(order["price"]))
                self.editing_order_id = order["id"]
                self.status_label.config(text=f"Mengedit pesanan: {order_id}")
                break
        
        map_filename = item["values"][8]
        if os.path.exists(map_filename):
            try:
                self.map_frame.load_file(map_filename)
                logging.info(f"Peta dimuat: {map_filename}")
                self.status_label.config(text=f"Menampilkan peta: {map_filename}")
            except Exception as e:
                logging.error(f"Gagal memuat peta di aplikasi: {str(e)}")
                webbrowser.open(map_filename)
                self.status_label.config(text=f"Peta dibuka di browser: {map_filename}")
        else:
            messagebox.showerror("Error", "File peta tidak ditemukan.")
            self.status_label.config(text="File peta tidak ditemukan.")

    def export_to_csv(self):
        message = self.controller.export_to_csv()
        messagebox.showinfo("Sukses", message)
        self.status_label.config(text=message)

if __name__ == "__main__":
    root = tk.Tk()
    app = DeliveryUI(root)
    root.mainloop()