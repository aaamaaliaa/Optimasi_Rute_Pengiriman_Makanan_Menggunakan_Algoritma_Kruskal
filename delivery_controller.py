import folium
import webbrowser
from folium.plugins import PolyLineTextPath
from geopy.geocoders import Nominatim
import delivery_models as models
import uuid
import json
import os
import logging

logging.basicConfig(level=logging.DEBUG, filename="delivery.log", filemode="w",
                    format="%(asctime)s - %(levelname)s - %(message)s")

class DeliveryController:
    def __init__(self):
        self.depot = None
        self.points = []
        self.orders = []
        self.geolocator = Nominatim(user_agent="delivery_app_cirebon")
        self.geocache = self.load_cache()
        self.routes = {}

    def load_cache(self):
        """Memuat cache alamat dari file."""
        try:
            with open("geocache.json", "r") as f:
                return json.load(f)
        except:
            return {}

    def save_cache(self):
        """Menyimpan cache alamat ke file."""
        with open("geocache.json", "w") as f:
            json.dump(self.geocache, f)

    def geocode_address(self, address, progress_callback=None):
        """Mengubah alamat menjadi koordinat GPS."""
        full_address = f"{address}, Cirebon, Indonesia"
        logging.debug(f"Geocoding alamat: {full_address}")
        if full_address in self.geocache:
            logging.debug(f"Menggunakan cache untuk: {full_address}")
            return self.geocache[full_address]
        try:
            location = self.geolocator.geocode(full_address)
            if progress_callback:
                progress_callback()
            if not location:
                logging.error(f"Alamat tidak ditemukan: {full_address}")
                return None
            coords = (location.latitude, location.longitude)
            self.geocache[full_address] = coords
            self.save_cache()
            logging.debug(f"Koordinat ditemukan: {coords}")
            return coords
        except Exception as e:
            logging.error(f"Error geocoding {full_address}: {str(e)}")
            return None, f"Gagal mengambil koordinat: {str(e)}. Pastikan koneksi internet aktif."

    def set_depot(self, name, address, progress_callback=None):
        """Menetapkan lokasi dapur/restoran."""
        if not name or not address:
            return False, "Nama dan alamat dapur harus diisi."
        result = self.geocode_address(address, progress_callback)
        if isinstance(result, tuple) and len(result) == 2:
            coords, error = result, None
        else:
            coords, error = None, result
        if not coords:
            return False, error or "Alamat dapur tidak ditemukan. Tambahkan detail seperti 'Cirebon' atau nomor jalan."
        if not models.validate_coords(*coords):
            return False, "Alamat harus berada di wilayah Cirebon (lat: -6.9 hingga -6.5, lon: 108.4 hingga 108.7)."
        self.depot = {"name": name, "coords": coords}
        logging.info(f"Dapur ditetapkan: {name}, {coords}")
        return True, "Dapur berhasil ditetapkan."

    def add_or_update_order(self, order_id, courier, customer, customer_address, destination, destination_address, order, price, progress_callback=None):
        """Menambahkan atau memperbarui pesanan."""
        try:
            price = float(price)
            customer_coords = self.geocode_address(customer_address, progress_callback)
            if not customer_coords:
                return False, "Alamat pelanggan tidak ditemukan. Tambahkan detail seperti 'Cirebon'."
            if not models.validate_coords(*customer_coords):
                return False, "Alamat pelanggan harus di wilayah Cirebon."
            
            destination_coords = self.geocode_address(destination_address, progress_callback)
            if not destination_coords:
                return False, "Alamat pengiriman tidak ditemukan. Tambahkan detail seperti 'Cirebon'."
            if not models.validate_coords(*destination_coords):
                return False, "Alamat pengiriman harus di wilayah Cirebon."
            
            customer_exists = any(p["name"] == customer for p in self.points) or (self.depot and self.depot["name"] == customer)
            if not customer_exists:
                self.points.append({"name": customer, "coords": customer_coords})
            
            destination_exists = any(p["name"] == destination for p in self.points) or (self.depot and self.depot["name"] == destination)
            if not destination_exists:
                self.points.append({"name": destination, "coords": destination_coords})
            
            order_data = {
                "id": order_id or str(uuid.uuid4()),
                "courier": courier,
                "customer": customer,
                "customer_coords": customer_coords,
                "destination": destination,
                "destination_coords": destination_coords,
                "order": order,
                "price": price,
                "customer_address": customer_address,
                "destination_address": destination_address
            }
            
            if order_id:
                for i, o in enumerate(self.orders):
                    if o["id"] == order_id:
                        self.orders[i] = order_data
                        logging.info(f"Pesanan diperbarui: {order_id}")
                        break
            else:
                self.orders.append(order_data)
                logging.info(f"Pesanan baru: {order_data['id']}")
            
            return True, "Pesanan berhasil disimpan."
        except ValueError:
            return False, "Harga harus angka."
        except Exception as e:
            logging.error(f"Error menambah pesanan: {str(e)}")
            return False, f"Gagal: {str(e)}. Pastikan koneksi internet aktif."

    def calculate_route_for_order(self, order):
        """Menghitung rute untuk satu pesanan."""
        if not self.depot:
            return None, None, None, "Dapur belum ditetapkan."
        
        customer_coords = order["customer_coords"]
        destination_coords = order["destination_coords"]
        
        if order["customer"] == order["destination"]:
            points = [self.depot, {"name": order["destination"], "coords": destination_coords}]
            start_idx = 0
        else:
            points = [
                self.depot,
                {"name": order["customer"], "coords": customer_coords},
                {"name": order["destination"], "coords": destination_coords}
            ]
            start_idx = 0
        
        distance_matrix = models.create_distance_matrix(points)
        route, total_distance, segments = models.find_shortest_route(distance_matrix, num_vehicles=1, start_idx=start_idx)
        if route is None:
            logging.error(f"Gagal menghitung rute untuk pesanan: {order['id']}")
            return None, None, None, "Gagal menghitung rute."
        
        self.routes[order["id"]] = (points, route, total_distance, segments)
        logging.info(f"Rute dihitung untuk pesanan: {order['id']}")
        return points, route, (total_distance, segments[0], segments[1]), None

    def calculate_multi_drop_route(self):
        """Menghitung rute multi-drop untuk semua pesanan."""
        if not self.depot:
            return None, None, None, None, "Dapur belum ditetapkan."
        points = [self.depot] + self.points
        if len(points) < 2:
            return None, None, None, None, "Tambahkan setidaknya satu pesanan."
        
        distance_matrix = models.create_distance_matrix(points)
        route, total_distance, segments, mst_edges = models.find_multi_drop_route(points, distance_matrix)
        if route is None:
            logging.error("Gagal menghitung rute multi-drop.")
            return None, None, None, None, "Gagal menghitung rute."
        
        self.routes["multi_drop"] = (points, route, total_distance, segments, mst_edges)
        logging.info("Rute multi-drop dihitung.")
        return points, route, (total_distance, segments[0], segments[1]), mst_edges, None

    def generate_map_for_order(self, order, points, route, segment_distances, segment_times):
        """Membuat peta untuk satu pesanan."""
        filename = f"delivery_map_{order['id']}.html"
        logging.debug(f"Membuat peta: {filename}")
        m = folium.Map(location=(-6.7320, 108.5523), zoom_start=12, tiles="CartoDB positron")
        
        for i, point in enumerate(points):
            popup_content = f"<b>{point['name']}</b>"
            if point["name"] == order["customer"]:
                popup_content += f"<br>Pesanan: {order['order']}<br>Harga: Rp {order['price']:,.0f}"
            elif point["name"] == order["destination"] and order["customer"] != order["destination"]:
                popup_content += f"<br>Pengiriman: {order['order']}"
            folium.Marker(
                location=point['coords'],
                popup=folium.Popup(popup_content, max_width=200),
                icon=folium.Icon(color="red" if point["name"] == self.depot["name"] else "blue", icon="cloud")
            ).add_to(m)

        route_coords = [points[i]["coords"] for i in route]
        for i in range(len(route) - 1):
            segment = [route_coords[i], route_coords[i + 1]]
            popup_content = (
                f"<b>{points[route[i]]['name']} -> {points[route[i + 1]]['name']}</b><br>"
                f"Jarak: {segment_distances[i]:.2f} km<br>Waktu: {segment_times[i]:.2f} menit"
            )
            line = folium.PolyLine(segment, color="blue", weight=3, opacity=0.8)
            line.add_to(m)
            line.add_child(folium.Popup(popup_content, max_width=200))
            PolyLineTextPath(
                line,
                f"{segment_distances[i]:.2f} km",
                attributes={'fill': 'black', 'font-size': '12'},
                offset=-5
            ).add_to(m)
        
        m.save(filename)
        logging.info(f"Peta disimpan: {filename}")
        try:
            webbrowser.open(filename)
            logging.info(f"Peta dibuka: {filename}")
        except Exception as e:
            logging.error(f"Gagal membuka peta: {str(e)}")
        return filename

    def generate_map_for_multi_drop(self, points, route, segment_distances, segment_times, mst_edges):
        """Membuat peta untuk rute multi-drop dengan MST."""
        filename = "delivery_map_multi_drop.html"
        logging.debug(f"Membuat peta multi-drop: {filename}")
        m = folium.Map(location=(-6.7320, 108.5523), zoom_start=12, tiles="CartoDB positron")
        
        for i, point in enumerate(points):
            popup_content = f"<b>{point['name']}</b>"
            folium.Marker(
                location=point['coords'],
                popup=folium.Popup(popup_content, max_width=200),
                icon=folium.Icon(color="red" if point["name"] == self.depot["name"] else "blue")
            ).add_to(m)

        for u, v, weight in mst_edges:
            segment = [points[u]["coords"], points[v]["coords"]]
            popup_content = f"<b>{points[u]['name']} -> {points[v]['name']}</b><br>Jarak: {weight:.2f} km"
            line = folium.PolyLine(segment, color="green", weight=3, opacity=0.5, dash_array="5, 5")
            line.add_to(m)
            line.add_child(folium.Popup(popup_content, max_width=200))
            PolyLineTextPath(
                line,
                f"{weight:.2f} km",
                attributes={'fill': 'black', 'font-size': '12'},
                offset=-5
            ).add_to(m)

        route_coords = [points[i]["coords"] for i in route]
        for i in range(len(route) - 1):
            segment = [route_coords[i], route_coords[i + 1]]
            popup_content = (
                f"<b>{points[route[i]]['name']} -> {points[route[i + 1]]['name']}</b><br>"
                f"Jarak: {segment_distances[i]:.2f} km<br>Waktu: {segment_times[i]:.2f} menit"
            )
            line = folium.PolyLine(segment, color="blue", weight=3, opacity=0.8)
            line.add_to(m)
            line.add_child(folium.Popup(popup_content, max_width=200))
            PolyLineTextPath(
                line,
                f"{segment_distances[i]:.2f} km",
                attributes={'fill': 'black', 'font-size': '12'},
                offset=-5
            ).add_to(m)
        
        m.save(filename)
        logging.info(f"Peta multi-drop disimpan: {filename}")
        try:
            webbrowser.open(filename)
            logging.info(f"Peta multi-drop dibuka: {filename}")
        except Exception as e:
            logging.error(f"Gagal membuka peta: {str(e)}")
        return filename

    def generate_all_points_map(self):
        """Membuat peta dengan semua titik (dapur dan alamat)."""
        if not self.depot:
            return None, "Dapur belum ditetapkan."
        points = [self.depot] + self.points
        if not points:
            return None, "Tidak ada titik untuk ditampilkan."
        
        filename = "all_points_map.html"
        m = folium.Map(location=(-6.7320, 108.5523), zoom_start=12, tiles="CartoDB positron")
        
        for point in points:
            popup_content = f"<b>{point['name']}</b>"
            folium.Marker(
                location=point['coords'],
                popup=folium.Popup(popup_content, max_width=200),
                icon=folium.Icon(color="red" if point["name"] == self.depot["name"] else "blue")
            ).add_to(m)
        
        m.save(filename)
        logging.info(f"Peta semua titik disimpan: {filename}")
        try:
            webbrowser.open(filename)
            logging.info(f"Peta semua titik dibuka: {filename}")
        except Exception as e:
            logging.error(f"Gagal membuka peta: {str(e)}")
        return filename, None

    def export_to_csv(self):
        """Mengekspor data pesanan ke CSV."""
        data = []
        if "multi_drop" in self.routes:
            points, route, total_distance, (segment_distances, segment_times), _ = self.routes["multi_drop"]
            route_str = " -> ".join(points[i]["name"] for i in route)
            data.append({
                "ID": "Multi-Drop",
                "Kurir": self.orders[0]["courier"] if self.orders else "N/A",
                "Pelanggan": "Semua",
                "Tujuan": "Semua",
                "Pesanan": "; ".join(o["order"] for o in self.orders),
                "Harga": sum(o["price"] for o in self.orders),
                "Jarak": total_distance,
                "Waktu": sum(segment_times),
                "Rute": route_str
            })
        for order in self.orders:
            if order["id"] in self.routes:
                points, route, total_distance, (segment_distances, segment_times) = self.routes[order["id"]]
                data.append({
                    "ID": order["id"][:8],
                    "Kurir": order["courier"],
                    "Pelanggan": order["customer"],
                    "Tujuan": order["destination"],
                    "Pesanan": order["order"],
                    "Harga": order["price"],
                    "Jarak": total_distance,
                    "Waktu": sum(segment_times)
                })
        import pandas as pd
        pd.DataFrame(data).to_csv("orders.csv", index=False)
        logging.info("Pesanan diekspor ke orders.csv")
        return "Pesanan diekspor ke orders.csv"