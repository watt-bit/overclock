import random
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPen, QColor, QBrush, QRadialGradient, QFont

# Particle system classes for smoke puff effect
class Particle(QGraphicsEllipseItem):
    """Individual particle for visual effects"""
    
    def __init__(self, x, y, size=10, is_generator_smoke=False, parent=None):
        super().__init__(0, 0, size, size, parent)
        self.setPos(x - size/2, y - size/2)
        
        # Random velocity for natural movement
        self.dx = random.uniform(-1.5, 1.5)
        if is_generator_smoke:
            # Generator smoke has stronger upward movement
            self.dy = random.uniform(-3.0, -1.5)  # Stronger upward bias
        else:
            self.dy = random.uniform(-2.0, -0.5)  # Normal upward bias
        
        # Random alpha fade rate
        if is_generator_smoke:
            # Generator smoke lasts longer
            self.fade_rate = random.uniform(0.02, 0.05)  # Slower fade
            self.alpha = random.uniform(0.8, 1.0)  # Start more opaque
        else:
            self.fade_rate = random.uniform(0.05, 0.1)
            self.alpha = random.uniform(0.7, 1.0)
        
        # Random growth/shrink
        self.size_change = random.uniform(-0.1, 0.2)
        self.current_size = size
        
        # Random gray value (from dark to light gray)
        if is_generator_smoke:
            # Darker smoke for generator
            self.gray_value = random.randint(200, 250)
        else:
            self.gray_value = random.randint(90, 250)
        
        # Set initial appearance
        self.updateAppearance()
    
    def updateAppearance(self):
        """Update the particle's visual appearance"""
        # Create a radial gradient for a soft, smoke-like appearance
        gradient = QRadialGradient(self.current_size/2, self.current_size/2, self.current_size/2)
        
        # Semi-transparent gray color with random shade
        color = QColor(self.gray_value, self.gray_value, self.gray_value, int(self.alpha * 255))
        
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, QColor(self.gray_value, self.gray_value, self.gray_value, 0))  # Transparent at edges
        
        self.setBrush(QBrush(gradient))
        # Create a transparent pen (using QPen) instead of Qt.NoPen
        self.setPen(QPen(Qt.transparent))
    
    def update_particle(self):
        """Update particle position, size and opacity for animation"""
        # Move the particle
        self.setPos(self.x() + self.dx, self.y() + self.dy)
        
        # Fade the particle
        self.alpha -= self.fade_rate
        
        # Update size (expand or contract)
        self.current_size += self.size_change
        if self.current_size <= 0:
            self.current_size = 0.1  # Prevent negative size
        
        # Update the ellipse size
        self.setRect(0, 0, self.current_size, self.current_size)
        
        # Update appearance
        self.updateAppearance()
        
        # Return whether the particle is still visible
        return self.alpha > 0.1

class RevenueParticle(QGraphicsTextItem):
    """Text particle for displaying revenue increments"""
    
    def __init__(self, x, y, amount=1000, parent=None):
        super().__init__(f"+${amount:,}", parent)
        self.setPos(x, y)
        
        # Set a nice font
        font = QFont("Arial", 26)
        font.setBold(True)
        self.setFont(font)
        
        # Random velocity for natural movement (with upward bias)
        self.dx = random.uniform(-1.0, 1.0)
        self.dy = random.uniform(-7.5, -4.5)  # Always float upward
        
        # Random fade rate
        self.fade_rate = random.uniform(0.02, 0.04)
        self.alpha = 1.0
        
        # Set initial appearance
        self.updateAppearance()
    
    def updateAppearance(self):
        """Update the particle's visual appearance"""
        # Create HTML with a semi-transparent gray background and green text
        bg_alpha = int(self.alpha * 150)  # More transparent background
        text_alpha = int(self.alpha * 255)
        
        html = f'<span style="background-color: rgba(80, 80, 80, {bg_alpha}); padding: 2px 6px; border-radius: 4px; color: rgba(0, 170, 0, {text_alpha});">+$1,000 💸</span>'
        
        # Set the HTML content
        self.setHtml(html)
    
    def update_particle(self):
        """Update particle position and opacity for animation"""
        # Move the particle
        self.setPos(self.x() + self.dx, self.y() + self.dy)
        
        # Fade the particle
        self.alpha -= self.fade_rate
        
        # Update appearance
        self.updateAppearance()
        
        # Return whether the particle is still visible
        return self.alpha > 0.1

class ParticleSystem:
    """Manages a set of particles for visual effects"""
    
    def __init__(self, scene):
        self.scene = scene
        self.particles = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.setInterval(33)  # ~30 fps
    
    def create_puff(self, x, y, num_particles=12):
        """Create a puff of smoke particles at the given coordinates"""
        # Create particles
        for _ in range(num_particles):
            # Add random offset to create wider origin area
            offset_x = random.uniform(-75, 75)  # +/- 50px horizontal spread
            offset_y = random.uniform(-30, 30)  # +/- 30px vertical spread
            
            # Calculate particle position with offset
            particle_x = x + offset_x
            particle_y = y + offset_y
            
            # Create particle with random size
            size = random.uniform(8, 20)
            particle = Particle(particle_x, particle_y, size)
            self.scene.addItem(particle)
            self.particles.append(particle)
        
        # Start the animation timer if not already running
        if not self.timer.isActive():
            self.timer.start()
    
    def create_generator_smoke(self, x, y, intensity=1.0):
        """Create smoke particles from a generator based on its output intensity
        
        Args:
            x (float): X coordinate for smoke origin
            y (float): Y coordinate for smoke origin
            intensity (float): Intensity level from 0.0 to 1.0 controlling 
                               number of particles and size
        """
        # Calculate number of particles based on intensity
        # More intensity = more particles (between 2 and 15)
        base_particles = 2
        max_particles = 15
        num_particles = int(base_particles + (max_particles - base_particles) * intensity)
        
        # Create particles
        for _ in range(num_particles):
            # Tighter grouping at the origin point
            offset_x = random.uniform(-20, 20)
            offset_y = random.uniform(-10, 10)
            
            # Calculate particle position with offset
            particle_x = x + offset_x
            particle_y = y + offset_y
            
            # Size based on intensity (bigger particles for higher intensity)
            min_size = 10
            max_size = 25
            size = random.uniform(min_size, min_size + (max_size - min_size) * intensity)
            
            # Create particle specifically for generator smoke
            particle = Particle(particle_x, particle_y, size, is_generator_smoke=True)
            self.scene.addItem(particle)
            self.particles.append(particle)
        
        # Start the animation timer if not already running
        if not self.timer.isActive():
            self.timer.start()
    
    def create_revenue_popup(self, x, y, amount=1000):
        """Create a revenue popup at the given coordinates"""
        # Create the revenue particle
        particle = RevenueParticle(x, y, amount)
        self.scene.addItem(particle)
        self.particles.append(particle)
        
        # Start the animation timer if not already running
        if not self.timer.isActive():
            self.timer.start()
    
    def update_particles(self):
        """Update all particles and remove those that are no longer visible"""
        if not self.particles:
            self.timer.stop()
            return
            
        # Update each particle and keep only those that are still visible
        remaining_particles = []
        for particle in self.particles:
            if particle.update_particle():
                remaining_particles.append(particle)
            else:
                self.scene.removeItem(particle)
        
        self.particles = remaining_particles
        
        # Stop the timer if all particles are gone
        if not self.particles:
            self.timer.stop() 