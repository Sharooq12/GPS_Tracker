import pandas as pd
from PIL import Image, ImageDraw, ImageTk, ImageFont
import tkinter as tk
from tkinter import ttk
import random
import math

# Constants
POINT_SIZE = 8
UPDATE_INTERVAL = 100
current_frame = 0
image_width, image_height = 0, 0
new_image = None
geofence_coordinates = {}
geofence_labels = []
tree = None
num_trucks = 10
show_entire_movement = False

def generate_truck_ids_and_colors(num_trucks):
    truck_ids = [f"Truck {i + 1}" for i in range(num_trucks)]
    truck_colors = [((i * 30) % 256, (i * 50) % 256, (i * 70) % 256, 255) for i in range(num_trucks)]
    return truck_ids, truck_colors

def draw_geofences(image_draw):
    for plant, geofences in geofence_coordinates.items():
        for geofence, coords in geofences.items():
            pixel_coords = [convert_to_pixels(lat, lon) for lat, lon in coords]
            image_draw.polygon(pixel_coords, outline="red")
            term_center = calculate_center(coords)
            draw_label(image_draw, f"{geofence}", term_center)


def convert_to_pixels(latitude, longitude):
    pixel_x = int((longitude - MIN_LONGITUDE) / (MAX_LONGITUDE - MIN_LONGITUDE) * image_width)
    pixel_y = int((1 - (latitude - MIN_LATITUDE) / (MAX_LATITUDE - MIN_LATITUDE)) * image_height)
    return pixel_x, pixel_y

def draw_corners(image_draw):
    for coord in [A, B, C, D]:
        x, y = convert_to_pixels(*coord)
        POINT_SIZE = 4
        image_draw.ellipse((x - POINT_SIZE, y - POINT_SIZE, x + POINT_SIZE, y + POINT_SIZE), fill="blue")

def read_coordinates_from_excel(file_path, sheet_name_layout, sheet_name_corners, sheet_name_geofence):
    df_corners = pd.read_excel(file_path, sheet_name=sheet_name_corners)
    A = (df_corners.loc[0, 'latitude'], df_corners.loc[0, 'longitude'])
    B = (df_corners.loc[1, 'latitude'], df_corners.loc[1, 'longitude'])
    C = (df_corners.loc[2, 'latitude'], df_corners.loc[2, 'longitude'])
    D = (df_corners.loc[3, 'latitude'], df_corners.loc[3, 'longitude'])

    df_layout = pd.read_excel(file_path, sheet_name=sheet_name_layout)
    coordinates_dict = {}
    for index, row in df_layout.iterrows():
        plant = row['Plant No.']
        term = row['term']
        point = row['points']
        latitude = row['latitude']
        longitude = row['longitude']
        color = row.get('color', None)
        if plant not in coordinates_dict:
            coordinates_dict[plant] = {}
        if term not in coordinates_dict[plant]:
            coordinates_dict[plant][term] = {'coordinates': [], 'color': color}
        coordinates_dict[plant][term]['coordinates'].append((latitude, longitude))

    df_layout1 = pd.read_excel(file_path, sheet_name=sheet_name_geofence)
    for index, row in df_layout1.iterrows():
        plant = row['Plant No.']
        geofence = row['Geofence']
        point = row['points']
        latitude = row['latitude']
        longitude = row['longitude']
        if plant not in geofence_coordinates:
            geofence_coordinates[plant] = {}
        if geofence not in geofence_coordinates[plant]:
            geofence_coordinates[plant][geofence] = []
        geofence_coordinates[plant][geofence].append((latitude, longitude))

    return coordinates_dict, A, B, C, D, geofence_coordinates

coordinates_dict, A, B, C, D, geofence_coordinates = read_coordinates_from_excel('Corner_update.xlsx', sheet_name_layout='Layout', sheet_name_corners='Corner', sheet_name_geofence='Geofence')

# Minimum and maximum latitude and longitude
MIN_LATITUDE = min(A[0], B[0], C[0], D[0])
MAX_LATITUDE = max(A[0], B[0], C[0], D[0])
MIN_LONGITUDE = min(A[1], B[1], C[1], D[1])
MAX_LONGITUDE = max(A[1], B[1], C[1], D[1])

def generate_random_coordinates():
    random_latitude = random.uniform(MIN_LATITUDE, MAX_LATITUDE)
    random_longitude = random.uniform(MIN_LONGITUDE, MAX_LONGITUDE)
    return random_latitude, random_longitude

def calculate_incremental_steps(current_coordinates, target_coordinates, total_steps):
    delta_latitude = (target_coordinates[0] - current_coordinates[0]) / total_steps
    delta_longitude = (target_coordinates[1] - current_coordinates[1]) / total_steps
    return delta_latitude, delta_longitude

def draw_polygon(image_draw):
    for plant, term_data in coordinates_dict.items():
        for term_name, term_info in term_data.items():
            layout_coords = [(float(lat), float(lon)) for lat, lon in term_info['coordinates']]
            if len(layout_coords) >= 2:
                color_str = str(term_info['color'])
                color_str_formatted = ",".join([color_str[i:i+3] for i in range(0, len(color_str), 3)])
                color_tuple = tuple(map(int, color_str_formatted.split(',')))
                image_draw.polygon([convert_to_pixels(lat, lon) for lat, lon in layout_coords], outline="white", fill=color_tuple)
                # term_center = calculate_center(layout_coords)
                # draw_label(image_draw, f"{term_name}", term_center)

def update_label(tree, truck_colors):
    global current_frame
    frame = create_frame(truck_colors)
    tk_image = ImageTk.PhotoImage(frame)
    label.config(image=tk_image)
    label.image = tk_image
    current_frame += 1
    root.after(UPDATE_INTERVAL, update_label, tree, truck_colors)

def on_button_click():
    selected_plant = plant_var.get()
    image_path = plant_images.get(selected_plant, plant_images.get(plant_options[0], "office1.PNG"))
    update_image(image_path)

def update_image(image_path):
    global new_image, image_width, image_height
    new_image = Image.open(image_path)
    new_image_tk = ImageTk.PhotoImage(new_image)
    label.config(image=new_image_tk)
    label.image = new_image_tk
    selected_image = Image.open(image_path)
    image_width, image_height = selected_image.size

def point_inside_geofence(point, geofence):
    latitude, longitude = point
    x = latitude
    y = longitude
    inside = False
    for i in range(len(geofence)):
        x1, y1 = geofence[i]
        x2, y2 = geofence[(i + 1) % len(geofence)]
        if ((y1 <= y < y2) or (y2 <= y < y1)) and (x <= x1 + (x2 - x1) * (y - y1) / (y2 - y1)):
            inside = not inside
    return inside

def draw_truck_id(frame, user_pixel, truck_id, truck_color):
    text_size = 12
    text_font = ImageFont.truetype("arial.ttf", text_size)
    text_color = "black"
    colored_truck_icon = change_truck_color("img/truck.png", truck_color)
    colored_truck_icon = colored_truck_icon.resize((2 * POINT_SIZE, 2 * POINT_SIZE))
    frame.paste(colored_truck_icon, (user_pixel[0] - POINT_SIZE, user_pixel[1] - POINT_SIZE), colored_truck_icon)
    frame_draw = ImageDraw.Draw(frame)
    frame_draw.text((user_pixel[0] + POINT_SIZE, user_pixel[1] - POINT_SIZE), truck_id, font=text_font, fill=text_color)

def change_truck_color(image_path, target_color):
    truck_icon = Image.open(image_path)
    truck_icon = truck_icon.convert("RGBA")
    alpha = truck_icon.split()[3]
    new_color_image = Image.new("RGBA", truck_icon.size, target_color)
    new_color_image.paste(alpha, (0, 0), alpha)
    return new_color_image

def calculate_center(coords):
    center_x = sum(lat for lat, lon in coords) / len(coords)
    center_y = sum(lon for lat, lon in coords) / len(coords)
    return center_x, center_y

def draw_label(image_draw, text, coordinates):
    label_size = 12
    label_font = ImageFont.truetype("arial.ttf", label_size)
    label_color = "black"
    pixel_coords = convert_to_pixels(*coordinates)
    image_draw.text((pixel_coords[0] - POINT_SIZE, pixel_coords[1] - POINT_SIZE), text, font=label_font, fill=label_color)

def create_table(container_frame3):
    y_scrollbar = ttk.Scrollbar(container_frame3, orient="vertical")
    tree = ttk.Treeview(container_frame3, columns=('ID', 'Truck'), show='headings', selectmode='browse', yscrollcommand=y_scrollbar.set)
    tree.heading('ID', text='ID')
    tree.heading('Truck', text='Truck')
    tree.column('ID', width=50, anchor='center')
    tree.column('Truck', width=50, anchor='center')
    for i in range(num_trucks):  # Use range(num_trucks) instead of num_trucks
        tree.insert('', i, values=(i + 1, f"Truck {i + 1}"))
    y_scrollbar.config(command=tree.yview)
    y_scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

def create_table1(container_frame):
    global tree
    y_scrollbar = ttk.Scrollbar(container_frame, orient="vertical")
    tree = ttk.Treeview(container_frame, columns=('Geofence', 'Count'), show='headings', selectmode='browse', yscrollcommand=y_scrollbar.set)
    tree.heading('Geofence', text='Geofence')
    tree.heading('Count', text='Count')
    tree.column('Geofence', width=70, anchor='center')
    tree.column('Count', width=30, anchor='center')
    y_scrollbar.config(command=tree.yview)
    y_scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

def create_frame(truck_colors):
    frame = new_image.copy()
    frame_draw = ImageDraw.Draw(frame)
    draw_corners(frame_draw)
    draw_polygon(frame_draw)
    draw_geofences(frame_draw)
    geofence_counts = {geofence: 0 for plant_geofences in geofence_coordinates.values() for geofence in plant_geofences}
    for i, truck in enumerate(trucks):
        delta_latitude, delta_longitude = calculate_incremental_steps(truck['current_coordinates'], truck['next_target_coordinates'], total_steps)
        previous_coordinates = truck['current_coordinates']
        truck['current_coordinates'] = (
            truck['current_coordinates'][0] + delta_latitude,
            truck['current_coordinates'][1] + delta_longitude
        )
        truck_x, truck_y = convert_to_pixels(*truck['current_coordinates'])
        truck_x -= POINT_SIZE
        truck_y -= POINT_SIZE
        draw_truck_id(frame, (truck_x, truck_y), f"Truck {i + 1}", truck_colors[i])
        if 'path' not in truck:
            truck['path'] = []
        truck['path'].append(truck['current_coordinates'])
        for plant, geofences in geofence_coordinates.items():
            for geofence, coords in geofences.items():
                if point_inside_geofence(truck['current_coordinates'], coords):
                    geofence_counts[geofence] += 1
                    break
        if math.isclose(truck['current_coordinates'][0], truck['next_target_coordinates'][0], rel_tol=1e-6) and math.isclose(truck['current_coordinates'][1], truck['next_target_coordinates'][1], rel_tol=1e-6):
            truck['next_target_coordinates'] = generate_random_coordinates()
    for i, truck in enumerate(trucks):
        if show_entire_movement and 'path' in truck:
            path = truck['path']
            if len(path) > 1:
                for j in range(len(path) - 1):
                    start_pixel_coords = convert_to_pixels(*path[j])
                    end_pixel_coords = convert_to_pixels(*path[j + 1])
                    frame_draw.line([start_pixel_coords, end_pixel_coords], fill=truck_colors[i], width=2)
        elif not show_entire_movement and 'previous_coordinates' in truck:
            previous_pixel_coords = convert_to_pixels(*truck['previous_coordinates'])
            current_pixel_coords = convert_to_pixels(*truck['current_coordinates'])
            frame_draw.line([previous_pixel_coords, current_pixel_coords], fill=truck_colors[i], width=2)
    for i, (geofence, count) in enumerate(geofence_counts.items()):
        update_geofence_count(i, geofence, count, tree)
    return frame

def toggle_movement():
    global show_entire_movement
    show_entire_movement = not show_entire_movement
    if show_entire_movement:
        toggle_button.config(image=on_image)
    else:
        toggle_button.config(image=off_image)


def update_geofence_count(index, geofence, count, tree):
    global geofence_labels
    if index < len(tree.get_children()):
        tree.item(tree.get_children()[index], values=(geofence, count))
    else:
        tree.insert('', index, values=(geofence, count))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("GPS System")

    trucks = [{'current_coordinates': generate_random_coordinates(), 'next_target_coordinates': generate_random_coordinates()} for _ in range(num_trucks)]
    total_steps = 100

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    background_image = Image.open("img/bg.jpg")
    background_image = background_image.resize((screen_width, screen_height), Image.LANCZOS)
    background_image_tk = ImageTk.PhotoImage(background_image)
    background_label = tk.Label(root, image=background_image_tk)
    background_label.place(relwidth=1, relheight=1)

    heading_label = tk.Label(root, text="GeoPath Tracker ", font=("Helvetica", 16, "bold"), bg="white")
    heading_label.place(relx=0.5, rely=0.02, anchor=tk.N)

    container_frame = tk.Frame(root, bg="white", bd=5)
    container_frame.place(relx=0.04, rely=0.07, relwidth=0.9, relheight=0.9)

    right_frame = tk.Frame(container_frame, bg="white")
    right_frame.place(relx=0.84, rely=0, relwidth=0.5, relheight=1)

    left_frame = tk.Frame(container_frame, bg="white")
    left_frame.place(relx=0, rely=0, relwidth=0.835, relheight=1)

    label = tk.Label(left_frame)
    label.place(relx=0.01, rely=0.5, anchor=tk.W)

    separator_line = tk.Canvas(container_frame, bg="black", width=2, height=container_frame.winfo_height())
    separator_line.place(relx=0.835, rely=0)

    plant_options = ["Plant 1"]
    plant_images = {
        "Plant 1": "img/greybg.PNG",
    }
    plant_var = tk.StringVar(root)
    plant_var.set(plant_options[0])

    dropdown_style = ttk.Style()
    dropdown_style.configure('TCombobox', padding=6, relief="flat", font=("Helvetica", 18))

    dropdown = ttk.Combobox(right_frame, textvariable=plant_var, values=plant_options, style='TCombobox', font=("Helvetica", 14))
    dropdown.place(relx=0, rely=0.04, relwidth=0.32, relheight=0.06, anchor=tk.W)

    select_button = ttk.Button(right_frame, text="Select", command=on_button_click)
    select_button.place(relx=0, rely=0.11, relwidth=0.32, relheight=0.06, anchor=tk.W)

    container_frame1 = tk.Frame(right_frame, bg="grey", bd=5)
    container_frame1.place(relx=0, rely=0.16, relwidth=0.32, relheight=0.83)

    container_frame2 = tk.Frame(container_frame1, bg="white", bd=5)
    container_frame2.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=0.42)
    create_table1(container_frame2)

    container_frame3 = tk.Frame(container_frame1, bg="white", bd=5)
    container_frame3.place(relx=0.0, rely=0.43, relwidth=1.0, relheight=0.4)
    create_table(container_frame3)

    # Load images for the on and off states
    on_image = tk.PhotoImage(file="img/on.png")
    off_image = tk.PhotoImage(file="img/off.png")

    history_label = tk.Label(container_frame1, text="History Tracking", font=("Helvetica", 16, "bold"), bg="white")
    history_label.place(relx=0.0, rely=0.84, relwidth=1.0, relheight=0.07)

    toggle_button = tk.Button(container_frame1, image=off_image, command=toggle_movement, bd=0)
    toggle_button.place(relx=0.0, rely=0.9, relwidth=1.0, relheight=0.1)

    truck_ids, truck_colors = generate_truck_ids_and_colors(num_trucks)
    on_button_click()
    update_label(tree, truck_colors)
    root.mainloop()

