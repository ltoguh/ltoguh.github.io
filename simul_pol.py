# -*- coding: utf-8 -*-
"""
Created on Tue Jun 24 09:48:05 2025

@author: hugol
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import random

class BirefringentMicroscopeSimulator:
    """
    Simulateur de microscope à polarisation avec objets biréfringents
    Affichage en temps réel avec contrôle de l'analyseur
    """
    
    def __init__(self, master):
        self.master = master
        master.title("🔬 Simulateur de Microscope à Polarisation - Temps Réel")
        master.geometry("800x700")
        
        # Paramètres de l'image
        self.image_width = 500
        self.image_height = 500
        
        # Paramètres physiques
        self.wavelengths_nm = {'R': 650, 'G': 550, 'B': 450}
        
        # Variables de contrôle
        self.analyzer_angle = tk.DoubleVar(value=0)
        self.animation_running = False
        self.update_pending = False
        
        # Génération des cartes d'échantillon
        # The sample generation is performed here.
        # This will call the methods that add different types of birefringent domains.
        self.retardance_map_nm, self.orientation_map = self._generate_enhanced_sample()
        
        # Interface utilisateur
        self._setup_ui()
        
        # Image initiale
        self._update_image_async()
        
    def _generate_enhanced_sample(self):
        """
        Génère un échantillon biréfringent avec différents types de domaines.
        This method orchestrates the creation of various sample features.
        """
        retardance_map = np.zeros((self.image_height, self.image_width), dtype=float)
        orientation_map = np.zeros((self.image_height, self.image_width), dtype=float)
        
        # Type 1: Domaines de Voronoi (cristaux irréguliers)
        # Adds irregular crystal-like domains using Voronoi partitioning.
        self._add_voronoi_domains(retardance_map, orientation_map, 50, 0, 1200)
        
        # # Type 2: Fibres orientées (polymères)
        # # This method is currently commented out, so it won't add fiber-like structures.
        # # To re-enable, uncomment the line below.
        # self._add_fiber_domains(retardance_map, orientation_map)
        
        # Type 3: Domaines radiaux (sphérolites)
        # Adds spherulite-like structures with radial orientation.
        self._add_radial_domains(retardance_map, orientation_map, 8)
        
        # Type 4: Bandes périodiques (lamelles)
        # This line is commented out as requested by the user to remove horizontal
        # and vertical periodic bands from the sample.
        # self._add_periodic_bands(retardance_map, orientation_map)
        
        return retardance_map, orientation_map
    
    def _add_voronoi_domains(self, retardance_map, orientation_map, num_grains, min_opd, max_opd):
        """
        Ajoute des domaines de type Voronoi à l'échantillon.
        Chaque pixel est attribué au domaine de point de semence le plus proche.
        """
        # Generate random seed points for Voronoi cells.
        seed_points = []
        for _ in range(num_grains):
            x = random.randint(0, self.image_width - 1)
            y = random.randint(0, self.image_height - 1)
            opd = np.random.uniform(min_opd, max_opd) # Optical Path Difference
            orientation = np.random.uniform(0, math.pi) # Orientation angle
            seed_points.append(((x, y), opd, orientation))
        
        # Assign each pixel to the closest seed point's properties.
        for y in range(self.image_height):
            for x in range(self.image_width):
                min_dist_sq = float('inf')
                closest_opd = 0.0
                closest_orientation = 0.0
                
                for (sx, sy), opd, orientation in seed_points:
                    dist_sq = (x - sx)**2 + (y - sy)**2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_opd = opd
                        closest_orientation = orientation
                
                # Update map only if the new OPD is greater (allows layering of features).
                retardance_map[y, x] = max(retardance_map[y, x], closest_opd)
                if retardance_map[y, x] == closest_opd:
                    orientation_map[y, x] = closest_orientation
    
    # def _add_fiber_domains(self, retardance_map, orientation_map):
    #     """
    #     Ajoute des fibres orientées à l'échantillon.
    #     Currently commented out and not active.
    #     """
    #     num_fibers = 0 # Set to 0, so no fibers are generated even if uncommented.
    #     for _ in range(num_fibers):
    #         # Position et orientation de la fibre
    #         start_x = random.randint(0, self.image_width)
    #         start_y = random.randint(0, self.image_height)
    #         angle = random.uniform(0, math.pi)
    #         length = random.randint(80, 200)
    #         width = random.randint(8, 20)
    #         opd = random.uniform(800, 1800)
            
    #         # Dessiner la fibre
    #         for i in range(length):
    #             x = int(start_x + i * math.cos(angle))
    #             y = int(start_y + i * math.sin(angle))
                
    #             for dx in range(-width//2, width//2 + 1):
    #                 for dy in range(-width//2, width//2 + 1):
    #                     nx, ny = x + dx, y + dy
    #                     if 0 <= nx < self.image_width and 0 <= ny < self.image_height:
    #                         if dx*dx + dy*dy <= (width/2)**2:
    #                             retardance_map[ny, nx] = max(retardance_map[ny, nx], opd)
    #                             if retardance_map[ny, nx] == opd:
    #                                 orientation_map[ny, nx] = angle
    
    def _add_radial_domains(self, retardance_map, orientation_map, num_spherulites):
        """
        Ajoute des domaines radiaux (sphérolites) à l'échantillon.
        Ces domaines ont une orientation radiale et OPD décroissant du centre.
        """
        for _ in range(num_spherulites):
            center_x = random.randint(50, self.image_width - 50)
            center_y = random.randint(50, self.image_height - 50)
            max_radius = random.randint(30, 80)
            base_opd = random.uniform(300, 1000)
            
            # Iterate over a square region around the spherulite center.
            for y in range(max(0, center_y - max_radius), 
                          min(self.image_height, center_y + max_radius)):
                for x in range(max(0, center_x - max_radius), 
                              min(self.image_width, center_x + max_radius)):
                    
                    dx, dy = x - center_x, y - center_y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance <= max_radius:
                        # OPD decreases from center outwards.
                        opd = base_opd * (1 - distance / max_radius)
                        # Orientation is radial (angle from center).
                        orientation = math.atan2(dy, dx)
                        
                        # Only update if the new OPD is greater, allowing overlap.
                        if opd > retardance_map[y, x]:
                            retardance_map[y, x] = opd
                            orientation_map[y, x] = orientation
    
    def _add_periodic_bands(self, retardance_map, orientation_map):
        """
        Ajoute des bandes périodiques horizontales et verticales.
        This method is currently not called in _generate_enhanced_sample,
        thus these bands are not generated.
        """
        # Horizontal bands
        for y in range(0, self.image_height, 40): # Iterate every 40 pixels vertically
            if y + 15 < self.image_height: # Ensure band fits within image
                opd = random.uniform(400, 1200)
                orientation = random.uniform(0, math.pi)
                # Apply OPD, taking the maximum value to allow overlapping features
                retardance_map[y:y+15, :] = np.maximum(
                    retardance_map[y:y+15, :], opd)
                # Apply orientation only where the new OPD was set
                mask = retardance_map[y:y+15, :] == opd
                orientation_map[y:y+15, :][mask] = orientation
        
        # Vertical bands
        for x in range(0, self.image_width, 60): # Iterate every 60 pixels horizontally
            if x + 10 < self.image_width: # Ensure band fits within image
                opd = random.uniform(200, 800)
                orientation = random.uniform(0, math.pi)
                # Apply OPD, taking the maximum value
                retardance_map[:, x:x+10] = np.maximum(
                    retardance_map[:, x:x+10], opd)
                # Apply orientation only where the new OPD was set
                mask = retardance_map[:, x:x+10] == opd
                orientation_map[:, x:x+10][mask] = orientation
    
    def _setup_ui(self):
        """Configure l'interface utilisateur de l'application."""
        # Main frame for padding and overall layout.
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame to hold the microscope image display.
        image_frame = ttk.LabelFrame(main_frame, text="Échantillon Biréfringent", padding=10)
        image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Canvas widget where the simulated microscope image will be drawn.
        self.canvas = tk.Canvas(
            image_frame, 
            width=self.image_width, 
            height=self.image_height,
            bg="black", # Black background for a dark field microscope feel
            relief=tk.SUNKEN, # Sunken border for visual depth
            borderwidth=2
        )
        self.canvas.pack()
        
        # Frame for controls (slider and buttons).
        control_frame = ttk.LabelFrame(main_frame, text="Contrôles", padding=10)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Analyzer angle display and slider.
        analyzer_frame = ttk.Frame(control_frame)
        analyzer_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(analyzer_frame, text="Angle de l'Analyseur:").pack(side=tk.LEFT)
        
        self.angle_label = ttk.Label(analyzer_frame, text="0°", font=("Arial", 12, "bold"))
        self.angle_label.pack(side=tk.RIGHT)
        
        # Slider to control the analyzer angle from 0 to 180 degrees.
        self.analyzer_slider = ttk.Scale(
            control_frame,
            from_=0, to=180,
            orient=tk.HORIZONTAL,
            variable=self.analyzer_angle,
            command=self._on_angle_change, # Callback when slider value changes
            length=400 # Length of the slider
        )
        self.analyzer_slider.pack(fill=tk.X, pady=5)
        
        # Buttons for interaction: Reset, Animation, Stop, Key Angles.
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="🔄 Reset", 
                  command=self._reset_angle).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="▶️ Animation", 
                  command=self._start_animation).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="⏸️ Stop", 
                  command=self._stop_animation).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="🎯 Points Clés", 
                  command=self._show_key_angles).pack(side=tk.LEFT, padx=5)
        
        # Information section about the sample types.
        info_frame = ttk.LabelFrame(control_frame, text="Informations", padding=5)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_text = """
        🔬 Échantillon multi-domaines:
        • Domaines de Voronoi (cristaux irréguliers)
        • Sphérolites (structures radiales)
        """
        # Note: Fibres orientées and Bandes périodiques are removed/commented out from this description
        # to reflect the actual sample generation.
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, font=("Arial", 9)).pack()
        
        # Variable to hold the PhotoImage object, important for avoiding garbage collection.
        self.photo_image = None
    
    def _calculate_intensity_vectorized(self, analyzer_angle_deg):
        """
        Calcul vectorisé optimisé de l'intensité lumineuse pour tous les pixels.
        Utilise la formule de l'intensité en polarisation pour chaque canal RGB.
        """
        analyzer_rad = math.radians(analyzer_angle_deg) # Convert analyzer angle to radians
        
        # Initialize an empty RGB image array.
        rgb_image = np.zeros((self.image_height, self.image_width, 3), dtype=np.uint8)
        
        # Calculate intensity for each color channel (Red, Green, Blue).
        for i, (channel, wavelength_nm) in enumerate(self.wavelengths_nm.items()):
            # Calculate phase retardation (gamma) based on retardance map and wavelength.
            gamma_rad = (2 * math.pi * self.retardance_map_nm) / wavelength_nm
            
            # Optimized intensity formula for crossed polarizers,
            # considering the orientation of the birefringent material (theta)
            # and the analyzer angle (A).
            # The formula used here is I = I0 * [cos^2(A) - sin(2*theta)*sin(2*(A-theta))*sin^2(gamma/2)]
            # However, a common simplified formula for crossed polarizers is
            # I = I0 * sin^2(2*theta) * sin^2(gamma/2)
            # The code uses a slightly different form, potentially accounting for polarizer orientation,
            # but for true crossed polarizers with fixed polarizer at 0, the simple formula holds.
            # Given the original code's formula: cos_A**2 + sin_2theta * sin_2A_minus_2theta * sin_gamma_half_sq
            # Let's stick to the original code's calculation to maintain its behavior,
            # which appears to be a more general case.
            
            cos_A = math.cos(analyzer_rad)
            sin_2theta = np.sin(2 * self.orientation_map)
            sin_2A_minus_2theta = np.sin(2 * (analyzer_rad - self.orientation_map))
            sin_gamma_half_sq = np.sin(gamma_rad / 2)**2
            
            # Final intensity calculation.
            intensity = cos_A**2 + sin_2theta * sin_2A_minus_2theta * sin_gamma_half_sq
            
            # Clip intensity values between 0 and 1 and convert to 0-255 byte range.
            intensity = np.clip(intensity, 0, 1)
            rgb_image[:, :, i] = (intensity * 255).astype(np.uint8)
        
        return rgb_image
    
    def _on_angle_change(self, value):
        """
        Callback appelé lorsque l'angle de l'analyseur est modifié via le slider.
        Met à jour le label de l'angle et déclenche une mise à jour asynchrone de l'image.
        """
        angle = float(value)
        self.angle_label.config(text=f"{angle:.1f}°")
        
        # Debounce the update to avoid excessive updates during slider drag.
        if not self.update_pending:
            self.update_pending = True
            # Schedule the image update for a short delay (10ms).
            self.master.after(10, self._update_image_async)
    
    def _update_image_async(self):
        """
        Déclenche le calcul et la mise à jour de l'image en arrière-plan (thread séparé).
        Cela évite de bloquer l'interface utilisateur pendant les calculs.
        """
        self.update_pending = False # Reset the debounce flag.
        
        def calculate_and_update():
            try:
                angle = self.analyzer_angle.get() # Get current analyzer angle.
                image_data = self._calculate_intensity_vectorized(angle) # Perform heavy calculation.
                
                # Schedule the canvas update back on the main Tkinter thread.
                # Tkinter GUI operations must be done in the main thread.
                self.master.after(0, lambda: self._update_canvas(image_data))
            except Exception as e:
                # Basic error handling for calculation issues.
                print(f"Erreur lors du calcul: {e}")
        
        # Start the calculation in a new daemon thread, so it won't prevent program exit.
        threading.Thread(target=calculate_and_update, daemon=True).start()
    
    def _update_canvas(self, image_data):
        """
        Met à jour le widget Tkinter Canvas avec les nouvelles données d'image.
        """
        try:
            # Convert NumPy array to PIL Image.
            img = Image.fromarray(image_data, mode='RGB')
            # Convert PIL Image to Tkinter PhotoImage.
            self.photo_image = ImageTk.PhotoImage(image=img)
            
            # Clear previous image from canvas and draw the new one.
            self.canvas.delete("all")
            self.canvas.create_image(
                self.image_width//2, # Center X position
                self.image_height//2, # Center Y position
                image=self.photo_image # The image object
            )
            
            # Keep a reference to the PhotoImage to prevent it from being garbage-collected.
            self.canvas.image = self.photo_image
            
        except Exception as e:
            # Basic error handling for canvas update issues.
            print(f"Erreur lors de la mise à jour du canvas: {e}")
    
    def _reset_angle(self):
        """
        Réinitialise l'angle de l'analyseur à 0 degrés.
        """
        self.analyzer_angle.set(0)
    
    def _start_animation(self):
        """
        Démarre l'animation automatique de l'angle de l'analyseur.
        """
        if not self.animation_running: # Only start if not already running.
            self.animation_running = True
            # Start the animation loop in a new thread.
            threading.Thread(target=self._animate, daemon=True).start()
    
    def _stop_animation(self):
        """
        Arrête l'animation automatique de l'angle de l'analyseur.
        """
        self.animation_running = False # Set flag to stop the animation loop.
    
    def _animate(self):
        """
        Boucle d'animation qui fait varier l'angle de l'analyseur de 0 à 180 degrés
        et vice-versa.
        """
        angle = self.analyzer_angle.get() # Get current angle to ensure smooth start.
        direction = 1 # Initial direction: incrementing angle.
        
        while self.animation_running:
            angle += direction * 0.5 # Increment/decrement angle by 0.5 degrees.
            
            # Reverse direction if angle reaches bounds (0 or 180).
            if angle >= 180:
                angle = 180
                direction = -1
            elif angle <= 0:
                angle = 0
                direction = 1
            
            # Update the Tkinter variable in the main thread.
            self.master.after(0, lambda a=angle: self.analyzer_angle.set(a))
            time.sleep(0.02) # Pause for 20ms (~50 FPS) to control animation speed.
    
    def _show_key_angles(self):
        """
        Anime l'analyseur pour passer par des angles clés (0, 45, 90, 135, 180 degrés).
        """
        key_angles = [0, 45, 90, 135, 180] # Define the key angles.
        
        def show_angles():
            for angle in key_angles:
                # Check if manual animation was started (e.g., via slider drag)
                # If so, stop this automatic sequence.
                if not self.animation_running:
                    self.master.after(0, lambda a=angle: self.analyzer_angle.set(a))
                    time.sleep(1.5) # Pause at each key angle for 1.5 seconds.
                else:
                    # If animation_running becomes true during this loop, break.
                    break
        
        # Start the key angles sequence in a new thread.
        threading.Thread(target=show_angles, daemon=True).start()

class BirefringentMicroscopeApp:
    """
    Classe principale pour lancer l'application du simulateur de microscope.
    """
    
    def __init__(self):
        self.root = tk.Tk() # Create the main Tkinter window.
        self.simulator = BirefringentMicroscopeSimulator(self.root) # Instantiate the simulator.
        
        # Configure window properties.
        self.root.minsize(800, 700) # Minimum window size.
        self.root.configure(bg='#f0f0f0') # Light grey background.
        
        # Apply a ttk style theme for modern looking widgets.
        style = ttk.Style()
        style.theme_use('clam') # 'clam' theme provides a flat, modern look.
    
    def run(self):
        """
        Lance l'application Tkinter et affiche des informations de démarrage dans la console.
        """
        print("🔬 Simulateur de Microscope à Polarisation")
        print("=" * 50)
        print("✨ Fonctionnalités:")
        print("• Échantillon multi-domaines biréfringents")
        print("• Contrôle temps réel de l'analyseur")
        print("• Calculs vectorisés optimisés")
        print("• Animation automatique")
        print("• Points d'observation clés")
        print("=" * 50)
        
        try:
            self.root.mainloop() # Start the Tkinter event loop.
        except KeyboardInterrupt:
            print("\n🛑 Application fermée par l'utilisateur") # Handle Ctrl+C exit.

# Point d'entrée de l'application
if __name__ == '__main__':
    app = BirefringentMicroscopeApp()
    app.run()
