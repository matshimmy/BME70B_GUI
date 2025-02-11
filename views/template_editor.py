from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np

class TemplateEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self.current_point = None
        self._build_ui()
        self.initialize_template()

    def _build_ui(self):
        layout = QVBoxLayout()
        
        # Create template plot
        self.template_plot = pg.PlotWidget(title="Template Editor")
        self.template_plot.setBackground('w')
        self.template_plot.setLabel('left', 'Amplitude', units='V')
        self.template_plot.setLabel('bottom', 'Time', units='s')
        self.template_plot.setXRange(0, 1)  # for now
        self.template_plot.setYRange(-1.5, 1.5)  # for now
        
        # Create scatter plot item for control points
        self.scatter = pg.ScatterPlotItem(size=10, pen=pg.mkPen('b'), brush=pg.mkBrush('b'))
        self.template_plot.addItem(self.scatter)
        
        # Create line plot for the curve
        self.curve = self.template_plot.plot(pen='b')
        
        # Connect mouse events
        self.scatter.sigClicked.connect(self._point_clicked)
        self.template_plot.scene().sigMouseClicked.connect(self._plot_clicked)
        self.template_plot.scene().sigMouseMoved.connect(self._mouse_moved)
        
        layout.addWidget(self.template_plot)
        self.setLayout(layout)

    def initialize_template(self):
        """Initialize with a flat line"""
        self.points = [
            {'pos': (0, 0), 'data': 1},
            {'pos': (1, 0), 'data': 2}
        ]
        self._update_template()

    def _update_template(self):
        """Update the template visualization"""
        if len(self.points) < 2:
            return
            
        # Sort points by x position
        self.points.sort(key=lambda p: p['pos'][0])
        
        # Extract x and y coordinates
        x = np.array([p['pos'][0] for p in self.points])
        y = np.array([p['pos'][1] for p in self.points])
        
        # Update scatter plot
        self.scatter.setData(x=x, y=y)
        
        # Create smooth curve using interpolation
        smooth_x = np.linspace(0, 1, 200)
        smooth_y = np.interp(smooth_x, x, y)
        self.curve.setData(smooth_x, smooth_y)

    def _point_clicked(self, _, points):
        """Handle clicking on existing points"""
        if len(points) > 0:
            self.current_point = points[0]

    def _plot_clicked(self, event):
        """Handle clicking on the plot to add new points"""
        if event.button() != 1:  # Left click only
            return
            
        pos = self.template_plot.plotItem.vb.mapSceneToView(event.scenePos())
        
        # Ensure x is within bounds
        x = np.clip(pos.x(), 0, 1)
        y = pos.y()
        
        # Add new point
        self.points.append({'pos': (x, y), 'data': len(self.points) + 1})
        self._update_template()

    def _mouse_moved(self, pos):
        """Handle dragging points"""
        if self.current_point is None:
            return
            
        pos = self.template_plot.plotItem.vb.mapSceneToView(pos)
        x = np.clip(pos.x(), 0, 1)
        y = pos.y()
        
        # Update point position
        for point in self.points:
            if point['data'] == self.current_point.data():
                point['pos'] = (x, y)
                break
                
        self._update_template()

    def get_template_data(self):
        """Return the current template data for use in simulation"""
        if len(self.points) < 2:
            return np.zeros(200), np.zeros(200)
            
        x = np.array([p['pos'][0] for p in self.points])
        y = np.array([p['pos'][1] for p in self.points])
        
        smooth_x = np.linspace(0, 1, 200)
        smooth_y = np.interp(smooth_x, x, y)
        
        return smooth_x, smooth_y

    def enable_editing(self, enabled: bool):
        """Enable or disable template editing"""
        self.template_plot.setEnabled(enabled)
