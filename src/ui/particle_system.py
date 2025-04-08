import random
from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPen, QColor, QBrush, QRadialGradient

# Particle system classes for smoke puff effect
class Particle(QGraphicsEllipseItem):
    """Individual particle for visual effects"""
    
    def __init__(self, x, y, size=10, parent=None):
        super().__init__(0, 0, size, size, parent)
        self.setPos(x - size/2, y - size/2)
        
        # Random velocity for natural movement
        self.dx = random.uniform(-1.5, 1.5)
        self.dy = random.uniform(-2.0, -0.5)  # Upward bias
        
        # Random alpha fade rate
        self.fade_rate = random.uniform(0.05, 0.1)
        self.alpha = random.uniform(0.7, 1.0)
        
        # Random growth/shrink
        self.size_change = random.uniform(-0.1, 0.2)
        self.current_size = size
        
        # Random gray value (from dark to light gray)
        self.gray_value = random.randint(40, 250)
        
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
            offset_x = random.uniform(-50, 50)  # +/- 50px horizontal spread
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